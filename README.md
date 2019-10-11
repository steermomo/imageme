这个项目是fork而来, 原项目5年(至2019年)未更新.

炼丹切图的时候总要看一下切得对不对, 而数据都不是放在本地跑, 用大内网的时候, 是在服务器上开了samba. 但是有些非局域网访问的时候(如GCP)就十分不方便, 用jupyter lab看图直接卡死.

项目初衷是--更方便地查看远程服务器的图片

[Simple image server](https://stackoverflow.com/questions/2463723/simple-image-server/26639617)
> I have a bunch of images that I need others to browse via a web browser in pretty much the same way as Apache-Gallery.
> I'd be able to dump all my images in a directory so that users hitting:
> http://server:port/directory
> would see small thumbnails and selecting an image would load it full size on a page with options to browse the previous or next image.
> I'm looking for a non Apache solution, much like the wonderfull Python simple http server, that can be launched anywhere with minimal configuration & fuss e.g.

Update:
1. 原项目太久, 只支持Python2
2. 原项目不支持分页, 目录下面几万张图片的时候疯狂加载.
3. 添加延迟加载


imageMe is a super simple image gallery server.

Think `python -m SimpleHTTPServer` for pictures.

![image.png](http://ww1.sinaimg.cn/large/dd456925gy1g7utn5uprtj20rp0ndwkb.jpg)

## Super Duper Easy One Line Usage

To run the image server on port 8000:

```bash
curl https://raw.githubusercontent.com/steermomo/imageme/master/imageme.py | python
```

## Manual Usage

### Step 1: Get the File

Get hold of a copy of `imageme.py`. For _really_ easy use put it in your `PATH`.

You could clone this repo:

```bash
> git clone https://github.com/steermomo/imageme.git
```

Or just grab the file directly:

```bash
> wget https://raw.githubusercontent.com/steermomo/imageme/master/imageme.py
```

### Step 2: Run imageMe

Run `imageme.py` from the root directory to serve from:

```bash
> cd /path/to/my/pics
> imageme.py
Processing .
Creating index file ./imageme.html
Processing ./photos
Creating index file ./photos/imageme.html
Processing ./photos/holiday
Creating index file ./photos/holiday/imageme.html
Processing ./photos/family
Creating index file ./photos/family/imageme.html
Processing ./super_secret_stay_out
Creating index file ./super_secret_stay_out/imageme.html
Your images are at http://127.0.0.1:8000/imageme.html
```

You can specify a port, just like you can with `SimpleHTTPServer`:

```bash
> imageme.py 5678
Processing .
...
Your images are at http://127.0.0.1:5678/imageme.html
```

## Browse and Enjoy

Hit the URL imageMe tells you in your browser, and have fun exploring.
