# Changelog

## v0.0.9-alpha

### Features
- Added nodes for downloading images from booru websites
- Added node for Ollama API
- Added node for vector storage
- Improved support for Graph nodes
- Added more miscellenous nodes (`FlattenList`,`LoadTextFileNode`,`JoinList`)

### Bug Fixes
- Fixed issue with `Display` node showing stretched images

## v0.0.8-alpha

### Features
- Added support for `Florence 2` models
- Added new `Display Text` and `Display Image` nodes for displaying text and images in the app
- `Display` node now deprecated
- First install don't need building using `wheel` anymore for python 3.10 and 3.11

### Bug Fixes
- Fixed issue with `Display` node showing stretched images

### Known Issues
- Naming of categories and nodes might be misleading and will be changed in the future
- Nodes can be connected in loop (which isn't supported)
- Missing undo/redo functionality
- Some nodes are not stopped immediately when the Stop button is pressed
- Missing type checking for input/output attributes on multiple nodes

## v0.0.7-alpha

### Features
- Added new `Graph node` which allows for using existing workflows as individual nodes

### Known Issues
- Naming of categories and nodes might be misleading and will be changed in the future
- Nodes can be connected in loop (which isn't supported)
- Missing undo/redo functionality
- Some nodes are not stopped immediately when the Stop button is pressed
- Missing type checking for input/output attributes on multiple nodes

## v0.0.6-alpha

### Features
- Added ability to duplicate nodes
- Improved visual representation of nodes
- Improved error visualization in nodes
- List input/output attributes now support multiple different types of data
- Added 'Unknown Node' which is used if the node is not found when loading a workflow
- Added new category of nodes "Storage" which includes nodes for saving and loading data for different types of storage

### Bug Fixes
- Nodes now being added at mouse position
- Fixed issue with linked 'Collector' and 'Iterator' nodes not working correctly
- Fixed issue with nodes connected to 'Collector' inputs losing their data when the iterator is finished

### Known Issues
- Naming of categories and nodes might be misleading and will be changed in the future
- Nodes can be connected in loop (which isn't supported)
- Missing undo/redo functionality
- Some nodes are not stopped immediately when the Stop button is pressed
- Missing type checking for input/output attributes on multiple nodes

## v0.0.5-alpha

### Features
- Added support for custom nodes

### Known Issues
- Naming of categories and nodes might be misleading and will be changed in the future
- Missing duplicate node functionality
- `Collector` node not working corectly if directly connected to `Iterator` node (workaround: connect any node between them)
- Node outputs which are also connected to `Collector` inputs might lose their data when the iterator is finished
- Nodes can be connected in loop (which isn't supported)
- Missing undo/redo functionality
- Nodes not being added at mouse position
- Some nodes are not stopped immediately when the Stop button is pressed

## v0.0.4-alpha

### Features
- Added ability to choose default cache location for models nodes (can be set in settings) menu or directly in the node
- Added different options for SaveToTextFile nodes (append, overwrite, error if exists, skip if exists)
- Added ability to specify where tags should be appended in JoinTags node (before or after)
- Added dedicated Changelog page in the app
- Added settings page in the app
- Improved node search
- Fixed issue with Display node not displaying list of files
- Added progress bar to other nodes
- Improved example workflows

### Bug Fixes
- Fixed sizing of some nodes and windows
- Check for updates menu item now works correctly

### Known Issues
- Naming of categories and nodes might be misleading and will be changed in the future
- Missing duplicate node functionality
- Missing custom node functionality
- `Collector` node not working corectly if directly connected to `Iterator` node (workaround: connect any node between them)
- Node outputs which are also connected to `Collector` inputs might lose their data when the iterator is finished
- Nodes can be connected in loop (which isn't supported)
- Missing undo/redo functionality
- Nodes not being added at mouse position
- Some nodes are not stopped immediately when the Stop button is pressed