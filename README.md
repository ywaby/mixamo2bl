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


workflow
1. download mixamo animation with skin.
2. import mixamo character 
3. download mixamo animations without skin to a folder.
4. select download folder
5. update

tips
- *.dae need skin (without skin will lose armature origin position).
- *.dae and *.fbx armture is not match, so don't mix use it.

<!-- ## TODO
- json config for rename bone 
- support dae
- add NLA option if need

BUG
- can not move frame after import
- dae import will break animation( reload blend fix it)
 -->