CREATED：2025.2

系统：Linux

## HomeAssistant部署

网上教程很多，此次采用Docker方式部署

1. 通过Docker拉取HA镜像，参考教程，可以在/etc/docker/daemon.json设置国内源进行加速
2. 由于后续需要安装HACS，而HACS首次集成和后续插件下载需要通过github，会出现网络连接问题。网上有一些解决方案，最终适合的方案是**给HA提供网络代理**
3. 服务器有本地代理，也不希望使用外部公用vpn，所以在启动HA容器时配置
```shell
docker run -d \
  --name homeassitant \
  --privileged \
  --restart=unless-stopped \
  -e TZ=Asia/Shanghai \
  -v ~/.config/homeassistant/config \
  --env HTTP_PROXY="http://127.0.0.1:9091/" \
  --env HTTPS_PROXY="http://127.0.0.1:9091/" \
  --env NO_PROXY="localhost,127.0.0.1" \
  --network=host \
  homeassistant/home-assistant:stable
```
注：当前使用HA版本为2025.2.4

## HACS安装
由于需要接入小米设备，需安装HACS再配置xiaomi miio

1. HACS安装可参考教程，参考[官方Container教程](https://www.hacs.xyz/docs/use/download/download/#to-download-hacs-container)
2. 此时遇到问题，按照指示会下载最新HACS极速版，在进行配置时，最终github验证后会出现代码报错（不知是否个例）
3. 解决办法，在HACS的github repo里下载较低版本HACS **2.0.1**版本，通过`docker cp`命令将zip文件复制到容器`custom_components`文件夹下，并解压到`hacs`文件夹
4. 后续按正常流程成功集成HACS，并以相同方法集成xiaomi miio auto

## 小米设备接入
可以xiaomi miio auto接入**支持miio协议的设备**，可参考官方github说明，也可通过[该网页](https://home.miot-spec.com/)搜索查看设备所支持的协议

1. 通过xiaomi miio auto添加设备，此时有两种接入方式，一种是账号自动接入，一种是局域网接入，核心诉求原则选择后者
2. 局域网接入需要设备host（局域网ip）和token，设备ip好查，token不容易获取
3. 参考各种教程，最终使用较为简单的方法，通过[该repo](https://github.com/PiotrMachowski/Xiaomi-cloud-tokens-extractor)
4. 选择手动跑脚本的方式
```shell
wget https://github.com/PiotrMachowski/Xiaomi-cloud-tokens-extractor/releases/latest/download/token_extractor.zip
unzip token_extractor.zip
cd token_extractor
```
```shell
pip3 install -r requirements.txt
python3 token_extractor.py
```
过程中需输入小米账密，最终输出设备信息，如下：
```
Devices found for server "cn" @ home "xxxxxxxx":
   ---------
   NAME:     Device 1
   ID:       xxxxxxxx
   MAC:      xx:xx:xx:xx:xx:xx
   IP:       192.168.31.xx
   TOKEN:    xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   MODEL:    xiaovv.camera.q1
   ---------
   NAME:     Device 2
   ID:       xxxxxxx
   MAC:      xx:xx:xx:xx:xx:xx
   IP:       192.168.31.xx
   TOKEN:    xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   MODEL:    yeelink.light.lamp4
   ---------
```
5. 将ip和token填入即可成功接入