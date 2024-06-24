import dearpygui.dearpygui as dpg
import hashlib
import os
from typing import Callable
import re
import enum

class AttributeKind(enum.Enum):
    VALUE = 0
    EVENT = 1
    GENERATOR = 2

class AttributeDefinition:

    def __init__(self, 
                 type_name:str|None=None,  
                 list: bool = False, 
                 optional: bool = False,
                 kind: AttributeKind = AttributeKind.VALUE
                 ):
        '''
        Attribute definition for node inputs and outputs.

        You can extend this class to define custom attribute types.

        Args:
            type (AttributeType): type of the attribute
            type_name (str, optional): name of the custom type, used when type is AttributeType.CUSTOM. Defaults to None.
            list (bool, optional): whether the attribute is a list. Defaults to False.
            kind (AttributeKind, optional): kind of the attribute. Defaults to AttributeKind.VALUE.
            file_select (bool, optional): if true, file select dialog will be shown when selecting the attribute. Defaults to False.
        '''

        self.type_name = type_name
        self.kind = kind
        self.list = list
        self.optional = optional

    @property
    def shape(self) -> int:
        '''
        Get shape for attribute definition.

        Returns:
            int: shape of the attribute
        '''

        if self.kind == AttributeKind.GENERATOR:
            return dpg.mvNode_PinShape_TriangleFilled 
        if self.kind == AttributeKind.EVENT:
            return dpg.mvNode_PinShape_Triangle
        if self.list:
            return dpg.mvNode_PinShape_QuadFilled if self.optional else dpg.mvNode_PinShape_Quad
        return dpg.mvNode_PinShape_CircleFilled if self.optional else dpg.mvNode_PinShape_Circle

    @property
    def color(self) -> tuple[int, int, int]:
        '''
        Get color for attribute definition.

        Returns:
            tuple[int, int, int]: color as RGB tuple
        '''
    
        # convert type_name to hash and use it as color
        hash_value = int(hashlib.sha256(self.type_name.encode()).hexdigest(), 16) % 10**8
        r = (hash_value & 0xFF0000) >> 16
        g = (hash_value & 0x00FF00) >> 8
        b = hash_value & 0x0000FF
        return (r, g, b)
    

    __theme = {}
    @property
    def theme(self) -> int:
        pin_theme = self.__theme.get(self.type_name)
        if pin_theme is not None:
            return pin_theme
        
        with dpg.theme() as pin_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvNodeCol_Pin, self.color, category=dpg.mvThemeCat_Nodes)
        
        self.__theme[self.type_name] = pin_theme
        return pin_theme

    def can_connect(self, other: "AttributeDefinition"):
        '''
        Check if this attribute can connect to another attribute.

        Args:
            other (AttributeDefinition): attribute definition to connect to
        '''
        if other.type_name == "any" or other.type_name == "any":
            return True
        if self.list != other.list:
            return False
        if self.type_name == other.type_name:
            return True

        return False
    
    def __str__(self):
        if self.list:
            return f"list[{self.type_name}]"
        else:
            return self.type_name
        
    def __eq__(self, other):
        if not hasattr(other, "type_name") or not hasattr(other, "list") or not hasattr(other, "generator"):
            return False
        return self.list == other.list and self.kind == other.kind and self.__str__() == other.__str__()
    
    def show_ui(self, node: "BaseNode", attribute_name: str, dpg_type: int, parent:str|int):
        '''
        Show ui for attribute definition.

        Args:
            node (BaseNode): node instance
            name (str): name of the attribute
            dpg_type (int): dearpygui type for the attribute (dpg.mvNode_Attr_Input, dpg.mvNode_Attr_Output, dpg.mvNode_Attr_Static)
            parent (int): tag of the parent container (node_attribute)

        Returns:
            None
        '''
        return dpg.add_text(f"{attribute_name}:{self}", parent=parent)
    
    def _get_default_value(self, type: int, attribute_name: str, node: "BaseNode"):
        if type == dpg.mvNode_Attr_Input:
            return node.default_inputs.get(attribute_name, None)
        if type == dpg.mvNode_Attr_Output:
            return node.default_outputs.get(attribute_name, None)
        return node.static_inputs.get(attribute_name, None)
    
    def _set_default_value(self, type: int, attribute_name: str, node: "BaseNode", value):
        if type == dpg.mvNode_Attr_Input:
            node.set_default_input(attribute_name, value)
        elif type == dpg.mvNode_Attr_Output:
            node.set_default_output(attribute_name, value)
        else:
            node.set_static_input(attribute_name, value)
        
    
class IntegerAttributeDefinition(AttributeDefinition):
    def __init__(self, min_value: int|None=None, max_value: int|None=None, list: bool = False, kind: AttributeKind = AttributeKind.VALUE):
        self.min_value = min_value
        self.max_value = max_value
        super().__init__(type_name="int", list=list, kind=kind)

    def _format_input(self, input):
        return int(input) if input is not None else 0
    
    def _format_output(self, output):
        return int(output) if output is not None else 0

    def show_ui(self, node: "BaseNode", attribute_name: str, dpg_type: int, parent:str|int):
        if self.list:
            return dpg.add_text(f"{attribute_name}:{self}", parent=parent)

        min_value = self.min_value if self.min_value is not None else 0
        max_value = self.max_value if self.max_value is not None else 100
        min_clamped = True if self.min_value is not None else False
        max_clamped = True if self.max_value is not None else False

        def on_input(sender, app_data):
            self._set_default_value(dpg_type, attribute_name, node, self._format_input(app_data))

        default_value = self._get_default_value(dpg_type, attribute_name, node)

        with dpg.group(horizontal=True, parent=parent) as group:
            input = dpg.add_input_int( 
                              min_value=min_value, min_clamped=min_clamped,
                              max_value=max_value, max_clamped=max_clamped,
                              width=100, callback=on_input, default_value=self._format_output(default_value))
            dpg.add_text(f"{attribute_name}:{self}")


        if dpg_type == dpg.mvNode_Attr_Input:
            node._on_input_connected += lambda input_name, _, __: dpg.hide_item(input) if input_name == attribute_name else None
            node._on_input_disconnected += lambda input_name, _, __: dpg.show_item(input) if input_name == attribute_name else None
        
        elif dpg_type == dpg.mvNode_Attr_Output:
            if attribute_name not in node.default_outputs:
                dpg.hide_item(input)

        return group

class FloatAttributeDefinition(AttributeDefinition):
    def __init__(self, min_value: float|None=None, max_value: float|None=None, list: bool = False, kind: AttributeKind = AttributeKind.VALUE):
        self.min_value = min_value
        self.max_value = max_value
        super().__init__(type_name="float", list=list, kind=kind)

    def _format_input(self, input):
        return float(input) if input is not None else 0.0
    
    def _format_output(self, output):
        return float(output) if output is not None else 0.0

    def show_ui(self, node: "BaseNode", attribute_name: str, dpg_type: int, parent:str|int):
        if self.list:
            return dpg.add_text(f"{attribute_name}:{self}", parent=parent)
        
        min_value = self.min_value if self.min_value is not None else 0.0
        max_value = self.max_value if self.max_value is not None else 1.0
        min_clamped = True if self.min_value is not None else False
        max_clamped = True if self.max_value is not None else False

        def on_input(sender, app_data):
            self._set_default_value(dpg_type, attribute_name, node, self._format_input(app_data))

        default_value = self._get_default_value(dpg_type, attribute_name, node)
        with dpg.group(horizontal=True, parent=parent) as group:
            input = dpg.add_input_float( 
                                width=100, 
                                min_value=min_value, min_clamped=min_clamped,
                                max_value=max_value, max_clamped=max_clamped,
                                callback=on_input, 
                                default_value=self._format_output(default_value))
            dpg.add_text(f"{attribute_name}:{self}")

        if dpg_type == dpg.mvNode_Attr_Input:
            node._on_input_connected += lambda input_name, _, __: dpg.hide_item(input) if input_name == attribute_name else None
            node._on_input_disconnected += lambda input_name, _, __: dpg.show_item(input) if input_name == attribute_name else None
        
        elif dpg_type == dpg.mvNode_Attr_Output:
            if attribute_name not in node.default_outputs:
                dpg.hide_item(input)
        
class StringAttributeDefinition(AttributeDefinition):
    def __init__(self, list: bool = False, kind: AttributeKind = AttributeKind.VALUE):
        super().__init__(type_name="str", list=list, kind=kind)

    def _format_input(self, input):
        if input is None:
            return "" if not self.list else []
        return input.split("\n") if self.list else input
    
    def _format_output(self, output):
        if output is None:
            return "" if not self.list else []
        return "\n".join(output) if self.list else output

    def show_ui(self, node: "BaseNode", attribute_name: str, dpg_type: int, parent:str|int):
        def on_input(sender, app_data):
            self._set_default_value(dpg_type, attribute_name, node, self._format_input(app_data))

        default_value = node.default_inputs.get(attribute_name, "") if dpg_type == dpg.mvNode_Attr_Input else node.default_outputs.get(attribute_name, "") if dpg_type == dpg.mvNode_Attr_Output else node.static_inputs.get(attribute_name, "")
        default_value = self._format_output(default_value)

        with dpg.group(horizontal=True, parent=parent) as group:
            input = dpg.add_input_text(width=100, callback=on_input, default_value=default_value, multiline=self.list)
            dpg.add_text(f"{attribute_name}:{self}")

        if dpg_type == dpg.mvNode_Attr_Input:
            node._on_input_connected += lambda input_name, _, __: dpg.hide_item(input) if input_name == attribute_name else None
            node._on_input_disconnected += lambda input_name, _, __: dpg.show_item(input) if input_name == attribute_name else None
         
        if dpg_type == dpg.mvNode_Attr_Output and attribute_name not in node.default_outputs:
            dpg.hide_item(input)
        
        return group

class FileAttributeDefinition(AttributeDefinition):
    def __init__(self,
                 allowed_extensions = [".*"], 
                 directory_selector=False,
                 initial_path="",
                 initial_file=".",
                 ):
        self.allowed_extensions = allowed_extensions
        self.directory_selector = directory_selector
        self.initial_path = initial_path
        self.initial_file = initial_file
        super().__init__(type_name="str", list=False, kind=AttributeKind.VALUE)

  
    def _on_file_select(self, sender, app_data, user_data):
        file_path_name: str = app_data.get("file_path_name", "")
        osdir = os.getcwd()

        # if file is in the same directory as the project, then remove the path,
        file_path_name = file_path_name.replace("\\", "/")
        osdir = osdir.replace("\\", "/")
        if file_path_name.startswith(osdir):
            file_path_name = file_path_name[len(osdir)+1:]

        dpg.set_value(user_data[0], file_path_name)
        user_data[1](sender,file_path_name)
        
    def _format_input(self, input):
        return str(input) if input is not None else ""
    
    def _format_output(self, output):
        return str(output) if output is not None else ""

    def show_ui(self, node: "BaseNode", attribute_name: str, dpg_type: int, parent:str|int):
       
        with dpg.file_dialog(label="Select file", callback=self._on_file_select, 
                             show=False,
                             default_path=self.initial_path,
                             default_filename=self.initial_file,
                             directory_selector=self.directory_selector,
                             width=700, height=400,
                             ) as file_dialog:
            for ext in self.allowed_extensions:
                dpg.add_file_extension(ext)

        def show_file_dialog(sender, app_data, user_data):
            dpg.set_item_user_data(file_dialog, user_data)
            dpg.show_item(file_dialog)

        def on_input(sender, app_data):
            self._set_default_value(dpg_type, attribute_name, node, self._format_input(app_data))

        default_value = self._get_default_value(dpg_type, attribute_name, node)

        with dpg.group(horizontal=True, parent=parent) as group:
            uuid = dpg.generate_uuid()
            button = dpg.add_button(label="[/]", callback=show_file_dialog, user_data=(uuid, on_input))
            input = dpg.add_input_text(width=100, 
                                       callback=on_input,
                                       tag=uuid, 
                                       default_value=self._format_output(default_value),
                                       multiline=self.list
                                       )
            dpg.add_text(f"{attribute_name}:{self}")

        if dpg_type == dpg.mvNode_Attr_Input:
            node._on_input_connected += lambda input_name, _, __: dpg.hide_item(button) if input_name == attribute_name else None
            node._on_input_connected += lambda input_name, _, __: dpg.hide_item(input) if input_name == attribute_name else None
            node._on_input_disconnected += lambda input_name, _, __: dpg.show_item(button) if input_name == attribute_name else None
            node._on_input_disconnected += lambda input_name, _, __: dpg.show_item(input) if input_name == attribute_name else None
        
        elif dpg_type == dpg.mvNode_Attr_Output:
            if attribute_name not in node.default_outputs:
                dpg.hide_item(button)
                dpg.hide_item(input)
        
class MultiFileAttributeDefinition(FileAttributeDefinition):
    def __init__(self,
                    allowed_extensions = [".*"], 
                    directory_selector=False,
                    initial_path="",
                    initial_file=".",
                    ):
        
        super().__init__(allowed_extensions, directory_selector, initial_path, initial_file)
        self.list = True

    def _on_file_select(self, sender, app_data, user_data):
        selections = app_data.get("selections", {}).items()

        # get files from selections
        files = [selection[1] for selection in selections]
        formatted_files = []
        
        for file_path_name in files:
            osdir = os.getcwd()

            # if file is in the same directory as the project, then remove the path,
            file_path_name = file_path_name.replace("\\", "/")
            osdir = osdir.replace("\\", "/")
            if file_path_name.startswith(osdir):
                file_path_name = file_path_name[len(osdir)+1:]

            formatted_files.append(file_path_name)

        text = "\n".join(formatted_files)
        dpg.set_value(user_data[0], text)

        user_data[1](sender, text)
        return
    
    def _format_input(self, input):
        return input.split("\n") if input is not None else []
    
    def _format_output(self, output):
        return "\n".join(output) if output is not None else ""
    
class BoolenAttributeDefinition(AttributeDefinition):
    def __init__(self, list: bool = False, kind: AttributeKind = AttributeKind.VALUE):
        super().__init__(type_name="bool", list=list, kind=kind)

    def _format_input(self, input):
        return bool(input) if input is not None else False
    
    def _format_output(self, output):
        return output if output is not None else False

    def show_ui(self, node: "BaseNode", attribute_name: str, dpg_type: int, parent:str|int):
        
        def on_input(sender, app_data):
            self._set_default_value(dpg_type, attribute_name, node, self._format_input(app_data))

        default_value = self._format_input(self._get_default_value(dpg_type, attribute_name, node))
        with dpg.group(horizontal=True, parent=parent) as group:
            checkbox = dpg.add_checkbox(callback=on_input, default_value=default_value)
            dpg.add_text(f"{attribute_name}:{self}")


        if dpg_type == dpg.mvNode_Attr_Input:
            node._on_input_connected += lambda input_name, _, __: dpg.hide_item(checkbox) if input_name == attribute_name else None
            node._on_input_disconnected += lambda input_name, _, __: dpg.show_item(checkbox) if input_name == attribute_name else None

        elif dpg_type == dpg.mvNode_Attr_Output:
            if attribute_name not in node.default_outputs:
                dpg.hide_item(checkbox)
                
        return group

class AnyAttributeDefinition(AttributeDefinition):
    def __init__(self, list: bool = False, kind: AttributeKind = AttributeKind.VALUE):
        super().__init__(type_name="any", list=list, kind=kind)
    
    def can_connect(self, other: AttributeDefinition):
        return True
    
class MultipleAttributeDefinition(AttributeDefinition):
    def __init__(self, types: list[AttributeDefinition],  kind: AttributeKind = AttributeKind.VALUE):
        self.types = types
        list: bool = False,
        super().__init__(type_name="multiple", list=list, kind=kind)
    
    def can_connect(self, other: AttributeDefinition):
        if self.type_name == "any" or other.type_name == "any":
            return True
        
        for type in self.types:
            if type.can_connect(other):
                return True
        return super().can_connect(other)
    
    def __str__(self):
        return "|".join(str(type) for type in self.types)
    
class ComboAttributeDefinition(AttributeDefinition):

    def __init__(self, values_callback: Callable[[], list[str]], allow_custom: bool = True):
        self.get_values = values_callback
        self.allow_custom = allow_custom
        super().__init__(type_name="str", list=False, kind=AttributeKind.VALUE)

    def _format_input(self, input):
        return str(input)
    
    def _format_output(self, output):
        return str(output)
    
    def show_ui(self, node: "BaseNode", attribute_name: str, dpg_type: int, parent:str|int):
        
        uuid = dpg.generate_uuid()
        text_uuid = dpg.generate_uuid()

        def on_input(sender, app_data):
            self._set_default_value(dpg_type, attribute_name, node, self._format_input(app_data))

        def on_selection(sender, app_data):
            dpg.set_value(uuid, app_data)
            dpg.set_value(text_uuid, app_data)
            on_input(sender, app_data)

        def on_press(sender, app_data):
            try:
                values = self.get_values()
                dpg.configure_item(uuid, items=values)
            except Exception as e:
                node._on_error.trigger(e)

        def on_text(sender, app_data):
            if self.allow_custom:
                on_input(sender, app_data)

        default_value = self._get_default_value(dpg_type, attribute_name, node)

        with dpg.group(horizontal=True, parent=parent) as group:
            dpg.add_combo(items=[default_value], callback=on_selection, default_value=default_value, tag=uuid, width=120, no_preview=self.allow_custom)
            dpg.add_input_text(width=100, tag=text_uuid, callback=on_text, default_value=default_value, show=self.allow_custom)
            dpg.add_text(f"{attribute_name}:{self}")


        with dpg.item_handler_registry() as handler:
            dpg.add_item_clicked_handler(callback=on_press)

        dpg.bind_item_handler_registry(uuid, handler)


        if dpg_type == dpg.mvNode_Attr_Input:
            node._on_input_connected += lambda input_name, _, __: dpg.hide_item(uuid) if input_name == attribute_name else None
            node._on_input_connected += lambda input_name, _, __: dpg.hide_item(text_uuid) if input_name == attribute_name else None
            node._on_input_disconnected += lambda input_name, _, __: dpg.show_item(uuid) if input_name == attribute_name else None
            node._on_input_disconnected += lambda input_name, _, __: dpg.show_item(text_uuid) if input_name == attribute_name else None

        elif dpg_type == dpg.mvNode_Attr_Output:
            if attribute_name not in node.default_outputs:
                dpg.hide_item(uuid)
                dpg.hide_item(text_uuid)
        
        return group
    
class DictAttributeDefinition(AttributeDefinition):
    def __init__(self, key_type: AttributeDefinition, value_type: AttributeDefinition, list: bool = False, kind: AttributeKind = AttributeKind.VALUE):
        self.key_type = key_type
        self.value_type = value_type
        type_name = f"dict[{key_type},{value_type}]"
        super().__init__(type_name=type_name, list=list, kind=kind)

    def can_connect(self, other: AttributeDefinition):
        if self.type_name == "any" or other.type_name == "any":
            return True
        if other.list != self.list:
            return False
        elif isinstance(other, DictAttributeDefinition):
            return self.key_type.can_connect(other.key_type) and self.value_type.can_connect(other.value_type)
        return super().can_connect(other)



class BaseNodeEvent:
    '''
    Event class for node events.
    '''

    def __init__(self):
        self.callbacks = []

    def register(self, callback: callable):
        self.callbacks.append(callback)

    def unregister(self, callback: callable):
        self.callbacks.remove(callback)

    def trigger(self, *args, **kwargs):
        for callback in self.callbacks:
            callback(*args, **kwargs)

    # overrite += operator
    def __iadd__(self, callback: callable):
        self.register(callback)
        return self
    
    # overrite -= operator
    def __isub__(self, callback: callable):
        self.unregister(callback)
        return self

class BaseNode:
    '''
    Base class for nodes in the graph.

    You should inherit from this class to create custom nodes.
    You have to override the following methods:
    - name(): returns the name of the node
    - run(): called when the node is executed

    You can also override the following methods and properties:

    - input_definitions(): returns the definitions for inputs
    - output_definitions(): returns the definitions for outputs
    - static_input_definitions(): returns the definitions for static inputs

    - category(): returns the category of the node
    - help(): returns the help text for the node
    - init(): called once before graph execution
    - cache: returns whether the node should cache its outputs

    You can also override constructor to set default values for inputs and metadata but it cannot have any other arguments.
    '''

    def __init__(self):

        self.default_inputs = {}
        '''
        Default values for inputs. These values will be used if the input is not connected to any other node.
        You can set default values for inputs by calling set_default_input() method in the constructor.
        '''

        self.static_inputs = {}
        '''
        Static values for inputs. These values are not connected to any other node and are used as the input value.
        You can set static values for inputs by calling set_static_input() method in the constructor.
        '''

        self.default_outputs = {}
        '''
        Default values for outputs. If is specified, then you can set these values in ui.
        '''

        self.metadata = {}
        '''
        Metadata for the node. This is used to store additional information about the node such as 'position'.
        You can store your own metadata by setting key-value pairs in this dictionary.
        '''

        self._on_init = BaseNodeEvent()
        '''
        Event triggered before the node is initialized.
        You can register callbacks to this event to perform custom actions before the node is initialized.

        Used by the graph editor to update node in ui.

        Args:
            None
        '''

        self._on_init_finished = BaseNodeEvent()
        '''
        Event triggered after the node is initialized.
        You can register callbacks to this event to perform custom actions after the node is initialized.

        Used by the graph editor to update node in ui.

        Args:
            None
        '''

        self._on_node_ready = BaseNodeEvent()
        '''
        Event triggered when the node is ready to be executed.

        Args:
            None
        '''


        self._on_run = BaseNodeEvent()
        '''
        Event triggered before the node is executed.
        You can register callbacks to this event to perform custom actions before the node is executed.

        Used by the graph editor to update node in ui.

        Args:
            None
        '''

        self._on_run_finished = BaseNodeEvent()
        '''
        Event triggered after the node is executed.
        You can register callbacks to this event to perform custom actions after the node is executed.

        Used by the graph editor to update node in ui.

        Args:
            None
        '''

        self._on_error = BaseNodeEvent()
        '''
        Event triggered when an error occurs during the node execution.
        You can register callbacks to this event to handle errors that occur during the node execution.

        Used by the graph editor to update node in ui.

        Args:
            error: exception that occurred during the node execution
        '''

        self._on_refresh = BaseNodeEvent()
        '''
        Event triggered when the node UI should be refreshed.
        You can register callbacks to this event to update the node UI.

        Used by the graph editor to update node in ui.
        '''

        self._on_input_connected = BaseNodeEvent()
        '''
        Event triggered when an input is connected to the node.
        You can register callbacks to this event to handle input connections.

        Used by the graph editor to update node in ui.

        Args:
            input_name: name of the input
            output_node: node that is connected to the input
            output_name: name of the output
        '''

        self._on_input_disconnected = BaseNodeEvent()
        '''
        Event triggered when an input is disconnected from the node.
        You can register callbacks to this event to handle input disconnections.

        Used by the graph editor to update node in ui.

        Args:
            input_name: name of the input
        '''

        self._on_output_connected = BaseNodeEvent()
        '''
        Event triggered when an output is connected to the node.
        You can register callbacks to this event to handle output connections.

        Used by the graph editor to update node in ui.

        Args:
            output_name: name of the output
            input_node: node that is connected to the output
            input_name: name of the input
        '''

        self._on_output_disconnected = BaseNodeEvent()
        '''
        Event triggered when an output is disconnected from the node.
        You can register callbacks to this event to handle output disconnections.

        Used by the graph editor to update node in ui.

        Args:
            output_name: name of the output
        '''

    @property
    def cache(self) -> bool:
        '''
        Returns whether the node should cache its outputs. This is used to avoid re-executing the node when its inputs have not changed.
        You can override this method to return False if the node should always be executed.

        Returns:
            bool: whether the node should cache its outputs
        '''

        return True
    
    @property
    def lazy_init(self) -> bool:
        '''
        Returns whether the node should be lazily initialized. This is used to avoid initializing the node until it is executed.
        You can override this method to return True if the node should be lazily initialized.

        Returns:
            bool: whether the node should be lazily initialized
        '''

        return False

    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        '''
        Returns the definitions for inputs. This is used to define the types of inputs for the node.
        You should override this method to return a dictionary with input names as keys and AttributeDefinition objects as values.

        Inputs are used to define the values that the node will receive when executed. Keys will match the keys in the dictionary passed as arguments to the run() method.

        Returns:
            dict[str, AttributeDefinition]: dictionary with input definitions
        '''
        return {}
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        '''
        Returns the definitions for outputs. This is used to define the types of outputs for the node.
        You should override this method to return a dictionary with output names as keys and AttributeDefinition objects as values.

        Outputs are used to define the values that the node will return when executed. Keys should match the keys in the dictionary returned by the run() method.

        Returns:
            dict[str, AttributeDefinition]: dictionary with output definitions
        '''
        return {}
    
    @property
    def static_input_definitions(self) -> dict[str, AttributeDefinition]:
        '''
        Returns the definitions for static inputs. This is used to define the types of static inputs for the node.
        You should override this method to return a dictionary with input names as keys and AttributeDefinition objects as values.

        Static inputs are used to define fixed values for inputs that are not connected to any other node.

        Returns:
            dict[str, AttributeDefinition]: dictionary with static input definitions
        '''
        return {}
    
    @property
    def help(self) -> str:
        '''
        Returns the help text for the node. This is displayed in the node UI as a tooltip.
        You can override this method to return custom help text for the node.

        Returns:
            str: help text for the node
        '''
        return f"{self.category()}/{self.name()} node\n" \
                f"Cache output: {self.cache}\n" \
                f"Lazy: {False}\n"

    def save_to_dict(self) -> dict:
        '''
        Save node data to a dictionary. This method is called when the node is saved to a file.
        You can override this method to have custom serialization logic.
        Use only basic types (str, int, float, bool, list, dict) to ensure compatibility with serialization.

        Returns:
            dict: dictionary with node data to save to a file
        '''
        return {
            "static_inputs": self.static_inputs,
            "default_inputs": self.default_inputs,
            "default_outputs": self.default_outputs,
            "metadata": self.metadata,
            "type": self.name(),
        }
    
    def load_from_dict(self, data: dict):
        '''
        Load node data from a dictionary. This method is called when the node is loaded from a file.
        You can override this method to have custom serialization logic.
        Use only basic types (str, int, float, bool, list, dict) to ensure compatibility with serialization.

        Args:
            data (dict): dictionary with node data loaded from a file
        '''

        self.static_inputs = {**self.static_inputs, **data.get("static_inputs", {})}
        self.default_inputs = {**self.default_inputs, **data.get("default_inputs", {})}
        self.default_outputs = {**self.default_outputs, **data.get("default_outputs", {})}
        self.metadata = data.get("metadata", {})
    
    @classmethod
    def name(cls) -> str:
        '''
        Returns the name of the node. This is used to identify the node in the graph.
        You have to override this method to return a custom name for the node.
        If you use same name as existing node, it will override definition of existing node.

        Returns:
            str: name of the node
        '''
        return re.sub(r'([a-z])([A-Z])', r'\1 \2', cls.__name__).title()
    
    @classmethod
    def category(cls) -> str:
        '''
        Returns the category of the node. This is used to group nodes in the UI.
        You can override this method to return a custom category for the node.

        Returns:
            str: category of the node
        '''
        return "General"
    
    def set_static_input(self, input_name: str, value):
        '''
        Set a static value for an input. This value will be used as the input value, regardless of whether the input is connected to any other node.
        This method is called everytime node is updated in ui.
        
        Args:
            input_name (str): name of the input
            value (object): static value for the input
        '''

        self.static_inputs[input_name] = value

    def set_default_input(self, input_name: str, value):
        '''
        Set a default value for an input. This value will be used if the input is not connected to any other node.
        This method is called everytime node is updated in ui.

        Args:
            input_name (str): name of the input
            value (object): default value for the input
        '''
        self.default_inputs[input_name] = value

    def set_default_output(self, output_name: str, value):
        '''
        Set a default value for an output.
        This method is called everytime node is updated in ui.

        Args:
            output_name (str): name of the output
            value (object): default value for the output
        '''
        self.default_outputs[output_name] = value

    def show_custom_ui(self, parent: int|str):
        '''
        Show custom UI for the node.
        You can override this method to show additional custom UI for the node.
        '''
        return None

    def refresh_ui(self):
        '''
        Trigger a refresh of the node UI.
        You should call this method when you want to update the UI of the node (e.g. after changing definitions for inputs/outputs/static_inputs).
        '''
        self._on_refresh.trigger()

    def init(self):
        '''
        Called once before graph execution.
        You can use this method to initialize or reset any internal state.

        Args:
            None

        Returns:
            None
        '''
        pass

    def run(self, **kwargs) -> dict[str, object]:
        '''
        Called when the node is executed.
        Can be executed multiple times during the graph execution.

        Args:
            **kwargs: keyword arguments for inputs, same as the keys in input_definitions

        Returns:
            dict[str, object]: dictionary with output values, keys should match the keys in output_definitions
        '''

        return {}
    
    def __str__(self) -> str:
        return f"{self.category()}/{self.name()}"
    

    class GeneratorExit():
        def __init__(self):
            pass

    class GeneratorContinue():
        def __init__(self):
            pass