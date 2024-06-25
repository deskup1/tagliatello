# Changelog

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