This is a blender addon for import and update mixamo animations.  

License under MIT.

## feature
- scale to 1, apply rotation
- merge animation
- rename bone and action
- add action to NLA
- add root motion

## install
git clone this repository to blender addon dir.

or download [zip](https://github.com/ywaby/mixamo2bl/archive/refs/heads/master.zip) then install in blender
```
preferences->addons->install
```

enable addon 
```
preferences->addons->search "Mixamo Import"
```

## usage
3D View > UI (Right Panel) > Mixamo Tab  

![screenshot](./screenshot.jpg)

1. download mixamo animation with skin.
2. import mixamo character 
3. download mixamo animations without skin to a folder.
4. select download folder
5. update


<!-- ## TODO
- json config for rename bone 
- support gltf
- add NLA option if need

BUG
- can not move frame after import
 -->