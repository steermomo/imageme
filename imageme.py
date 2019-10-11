#!/usr/bin/python
"""
imageMe is a super simple image gallery server.

Run imageme.py from the top level of an image directory to generate gallery
index HTML and run a SimpleHTTPServer on the localhost.

Imported as a module, use imageme.serve_dir(your_path) to do the same for any
directory programmatically. When run as entry point, imageme.serve_dir('.') is
what's called.
"""

# Dependencies
import base64
import io
import os
import re
import sys
import threading
# import SimpleHTTPServer
# import SocketServer
import socketserver
import http.server

from include import UNSUPPORTED_IMAGE_TYPE_DATA
# Attempt to import PIL - if it doesn't exist we won't be able to make use of
# some performance enhancing goodness, but imageMe will still work fine
PIL_ENABLED = False
try:
    print('Attempting to import from PIL...')
    from PIL import Image
    PIL_ENABLED = True
    print('Success! Enjoy your supercharged imageMe.')
except ImportError:
    print(
        'WARNING: \'PIL\' module not found, so you won\'t get all the ' +
        'performance you could out of imageMe. Install Pillow (' +
        'https://github.com/python-pillow/Pillow) to enable support.'
    )

# Constants / configuration
## Filename of the generated index files
INDEX_FILE_NAME = 'imageme.html'
## Regex for matching only image files
IMAGE_FILE_REGEX = '^.+\.(png|jpg|jpeg|tif|tiff|gif|bmp)$'
## Images per row of the gallery tables
IMAGES_PER_ROW = 5
## Resampling mode to use when thumbnailing
RESAMPLE = None if not PIL_ENABLED else Image.NEAREST
## Width in pixels of thumnbails generated with PIL
THUMBNAIL_WIDTH = 800


class BackgroundIndexFileGenerator:

    def __init__(self, dir_path):
        self.dir_path = dir_path
        self.thread = threading.Thread(target=self._process, args=())
        self.thread.daemon = True

    def _process(self):
        _create_index_files(self.dir_path)

    def run(self):
        self.thread.start()


def _clean_up(paths):
    """
    Clean up after ourselves, removing created files.

    @param {[String]} A list of file paths specifying the files we've created
        during run. Will all be deleted.

    @return {None}
    """
    print('Cleaning up')
    # Iterate over the given paths, unlinking them
    for path in paths:
        print('Removing %s' % path)
        os.unlink(path)


def _create_index_file(
        root_dir, location, image_files, dirs, force_no_processing=False):
    """
    Create an index file in the given location, supplying known lists of
    present image files and subdirectories.

    @param {String} root_dir - The root directory of the entire crawl. Used to
        ascertain whether the given location is the top level.

    @param {String} location - The current directory of the crawl. The index
        file will be created here.

    @param {[String]} image_files - A list of image file names in the location.
        These will be displayed in the index file's gallery.

    @param {[String]} dirs - The subdirectories of the location directory.
        These will be displayed as links further down the file structure.

    @param {Boolean=False} force_no_processing - If True, do not attempt to
        actually process thumbnails, PIL images or anything. Simply index
        <img> tags with original file src attributes.

    @return {String} The full path (location plus filename) of the newly
        created index file. Intended for usage cleaning up created files.
    """
    # Put together HTML as a list of the lines we'll want to include
    # Issue #2 exists to do this better than HTML in-code
    header_text = \
        'imageMe: ' + location + ' [' + str(len(image_files)) + ' image(s)]'
    html = [
        '<!DOCTYPE html>',
        '<html>',
        '    <head>',
        '        <title>imageMe</title>'
        '        <style>',
        '            html, body {margin: 0;padding: 0;}',
        '            .header {text-align: right;}',
        '            .content {',
        '                padding: 3em;',
        '                padding-left: 4em;',
        '                padding-right: 4em;',
        '            }',
        '            .image {max-width: 100%; border-radius: 0.3em;}',
        '            td {width: ' + str(100.0 / IMAGES_PER_ROW) + '%;}',
        '        </style>',
        '       <script> ',
        '           !function(a,b){var c=b(a,a.document);a.lazySizes=c,"object"==typeof module&&module.exports&&(module.exports=c)}("undefined"!=typeof window?window:{},function(a,b){"use strict";var c,d;if(function(){var b,c={lazyClass:"lazyload",loadedClass:"lazyloaded",loadingClass:"lazyloading",preloadClass:"lazypreload",errorClass:"lazyerror",autosizesClass:"lazyautosizes",srcAttr:"data-src",srcsetAttr:"data-srcset",sizesAttr:"data-sizes",minSize:40,customMedia:{},init:!0,expFactor:1.5,hFac:.8,loadMode:2,loadHidden:!0,ricTimeout:0,throttleDelay:125};d=a.lazySizesConfig||a.lazysizesConfig||{};for(b in c)b in d||(d[b]=c[b])}(),!b||!b.getElementsByClassName)return{init:function(){},cfg:d,noSupport:!0};var e=b.documentElement,f=a.Date,g=a.HTMLPictureElement,h="addEventListener",i="getAttribute",j=a[h],k=a.setTimeout,l=a.requestAnimationFrame||k,m=a.requestIdleCallback,n=/^picture$/i,o=["load","error","lazyincluded","_lazyloaded"],p={},q=Array.prototype.forEach,r=function(a,b){return p[b]||(p[b]=new RegExp("(\\s|^)"+b+"(\\s|$)")),p[b].test(a[i]("class")||"")&&p[b]},s=function(a,b){r(a,b)||a.setAttribute("class",(a[i]("class")||"").trim()+" "+b)},t=function(a,b){var c;(c=r(a,b))&&a.setAttribute("class",(a[i]("class")||"").replace(c," "))},u=function(a,b,c){var d=c?h:"removeEventListener";c&&u(a,b),o.forEach(function(c){a[d](c,b)})},v=function(a,d,e,f,g){var h=b.createEvent("Event");return e||(e={}),e.instance=c,h.initEvent(d,!f,!g),h.detail=e,a.dispatchEvent(h),h},w=function(b,c){var e;!g&&(e=a.picturefill||d.pf)?(c&&c.src&&!b[i]("srcset")&&b.setAttribute("srcset",c.src),e({reevaluate:!0,elements:[b]})):c&&c.src&&(b.src=c.src)},x=function(a,b){return(getComputedStyle(a,null)||{})[b]},y=function(a,b,c){for(c=c||a.offsetWidth;c<d.minSize&&b&&!a._lazysizesWidth;)c=b.offsetWidth,b=b.parentNode;return c},z=function(){var a,c,d=[],e=[],f=d,g=function(){var b=f;for(f=d.length?e:d,a=!0,c=!1;b.length;)b.shift()();a=!1},h=function(d,e){a&&!e?d.apply(this,arguments):(f.push(d),c||(c=!0,(b.hidden?k:l)(g)))};return h._lsFlush=g,h}(),A=function(a,b){return b?function(){z(a)}:function(){var b=this,c=arguments;z(function(){a.apply(b,c)})}},B=function(a){var b,c=0,e=d.throttleDelay,g=d.ricTimeout,h=function(){b=!1,c=f.now(),a()},i=m&&g>49?function(){m(h,{timeout:g}),g!==d.ricTimeout&&(g=d.ricTimeout)}:A(function(){k(h)},!0);return function(a){var d;(a=!0===a)&&(g=33),b||(b=!0,d=e-(f.now()-c),d<0&&(d=0),a||d<9?i():k(i,d))}},C=function(a){var b,c,d=99,e=function(){b=null,a()},g=function(){var a=f.now()-c;a<d?k(g,d-a):(m||e)(e)};return function(){c=f.now(),b||(b=k(g,d))}},D=function(){var g,l,m,o,p,y,D,F,G,H,I,J,K=/^img$/i,L=/^iframe$/i,M="onscroll"in a&&!/(gle|ing)bot/.test(navigator.userAgent),N=0,O=0,P=0,Q=-1,R=function(a){P--,(!a||P<0||!a.target)&&(P=0)},S=function(a){return null==J&&(J="hidden"==x(b.body,"visibility")),J||!("hidden"==x(a.parentNode,"visibility")&&"hidden"==x(a,"visibility"))},T=function(a,c){var d,f=a,g=S(a);for(F-=c,I+=c,G-=c,H+=c;g&&(f=f.offsetParent)&&f!=b.body&&f!=e;)(g=(x(f,"opacity")||1)>0)&&"visible"!=x(f,"overflow")&&(d=f.getBoundingClientRect(),g=H>d.left&&G<d.right&&I>d.top-1&&F<d.bottom+1);return g},U=function(){var a,f,h,j,k,m,n,p,q,r,s,t,u=c.elements;if((o=d.loadMode)&&P<8&&(a=u.length)){for(f=0,Q++;f<a;f++)if(u[f]&&!u[f]._lazyRace)if(!M||c.prematureUnveil&&c.prematureUnveil(u[f]))aa(u[f]);else if((p=u[f][i]("data-expand"))&&(m=1*p)||(m=O),r||(r=!d.expand||d.expand<1?e.clientHeight>500&&e.clientWidth>500?500:370:d.expand,c._defEx=r,s=r*d.expFactor,t=d.hFac,J=null,O<s&&P<1&&Q>2&&o>2&&!b.hidden?(O=s,Q=0):O=o>1&&Q>1&&P<6?r:N),q!==m&&(y=innerWidth+m*t,D=innerHeight+m,n=-1*m,q=m),h=u[f].getBoundingClientRect(),(I=h.bottom)>=n&&(F=h.top)<=D&&(H=h.right)>=n*t&&(G=h.left)<=y&&(I||H||G||F)&&(d.loadHidden||S(u[f]))&&(l&&P<3&&!p&&(o<3||Q<4)||T(u[f],m))){if(aa(u[f]),k=!0,P>9)break}else!k&&l&&!j&&P<4&&Q<4&&o>2&&(g[0]||d.preloadAfterLoad)&&(g[0]||!p&&(I||H||G||F||"auto"!=u[f][i](d.sizesAttr)))&&(j=g[0]||u[f]);j&&!k&&aa(j)}},V=B(U),W=function(a){var b=a.target;if(b._lazyCache)return void delete b._lazyCache;R(a),s(b,d.loadedClass),t(b,d.loadingClass),u(b,Y),v(b,"lazyloaded")},X=A(W),Y=function(a){X({target:a.target})},Z=function(a,b){try{a.contentWindow.location.replace(b)}catch(c){a.src=b}},$=function(a){var b,c=a[i](d.srcsetAttr);(b=d.customMedia[a[i]("data-media")||a[i]("media")])&&a.setAttribute("media",b),c&&a.setAttribute("srcset",c)},_=A(function(a,b,c,e,f){var g,h,j,l,o,p;(o=v(a,"lazybeforeunveil",b)).defaultPrevented||(e&&(c?s(a,d.autosizesClass):a.setAttribute("sizes",e)),h=a[i](d.srcsetAttr),g=a[i](d.srcAttr),f&&(j=a.parentNode,l=j&&n.test(j.nodeName||"")),p=b.firesLoad||"src"in a&&(h||g||l),o={target:a},s(a,d.loadingClass),p&&(clearTimeout(m),m=k(R,2500),u(a,Y,!0)),l&&q.call(j.getElementsByTagName("source"),$),h?a.setAttribute("srcset",h):g&&!l&&(L.test(a.nodeName)?Z(a,g):a.src=g),f&&(h||l)&&w(a,{src:g})),a._lazyRace&&delete a._lazyRace,t(a,d.lazyClass),z(function(){var b=a.complete&&a.naturalWidth>1;p&&!b||(b&&s(a,"ls-is-cached"),W(o),a._lazyCache=!0,k(function(){"_lazyCache"in a&&delete a._lazyCache},9)),"lazy"==a.loading&&P--},!0)}),aa=function(a){if(!a._lazyRace){var b,c=K.test(a.nodeName),e=c&&(a[i](d.sizesAttr)||a[i]("sizes")),f="auto"==e;(!f&&l||!c||!a[i]("src")&&!a.srcset||a.complete||r(a,d.errorClass)||!r(a,d.lazyClass))&&(b=v(a,"lazyunveilread").detail,f&&E.updateElem(a,!0,a.offsetWidth),a._lazyRace=!0,P++,_(a,b,f,e,c))}},ba=C(function(){d.loadMode=3,V()}),ca=function(){3==d.loadMode&&(d.loadMode=2),ba()},da=function(){if(!l){if(f.now()-p<999)return void k(da,999);l=!0,d.loadMode=3,V(),j("scroll",ca,!0)}};return{_:function(){p=f.now(),c.elements=b.getElementsByClassName(d.lazyClass),g=b.getElementsByClassName(d.lazyClass+" "+d.preloadClass),j("scroll",V,!0),j("resize",V,!0),a.MutationObserver?new MutationObserver(V).observe(e,{childList:!0,subtree:!0,attributes:!0}):(e[h]("DOMNodeInserted",V,!0),e[h]("DOMAttrModified",V,!0),setInterval(V,999)),j("hashchange",V,!0),["focus","mouseover","click","load","transitionend","animationend"].forEach(function(a){b[h](a,V,!0)}),/d$|^c/.test(b.readyState)?da():(j("load",da),b[h]("DOMContentLoaded",V),k(da,2e4)),c.elements.length?(U(),z._lsFlush()):V()},checkElems:V,unveil:aa,_aLSL:ca}}(),E=function(){var a,c=A(function(a,b,c,d){var e,f,g;if(a._lazysizesWidth=d,d+="px",a.setAttribute("sizes",d),n.test(b.nodeName||""))for(e=b.getElementsByTagName("source"),f=0,g=e.length;f<g;f++)e[f].setAttribute("sizes",d);c.detail.dataAttr||w(a,c.detail)}),e=function(a,b,d){var e,f=a.parentNode;f&&(d=y(a,f,d),e=v(a,"lazybeforesizes",{width:d,dataAttr:!!b}),e.defaultPrevented||(d=e.detail.width)&&d!==a._lazysizesWidth&&c(a,f,e,d))},f=function(){var b,c=a.length;if(c)for(b=0;b<c;b++)e(a[b])},g=C(f);return{_:function(){a=b.getElementsByClassName(d.autosizesClass),j("resize",g)},checkElems:g,updateElem:e}}(),F=function(){!F.i&&b.getElementsByClassName&&(F.i=!0,E._(),D._())};return k(function(){d.init&&F()}),c={cfg:d,autoSizer:E,loader:D,init:F,uP:w,aC:s,rC:t,hC:r,fire:v,gW:y,rAF:z}});'
        '       </script> ',
        '    </head>',
        '    <body>',
        '    <div class="content">',
        '        <h2 class="header">' + header_text + '</h2>'
    ]
    # Populate the present subdirectories - this includes '..' unless we're at
    # the top level
    directories = []
    if root_dir != location:
        directories = ['..']
    directories += dirs
    if len(directories) > 0:
        html.append('<hr>')
    # For each subdirectory, include a link to its index file
    for directory in directories:
        link = directory + '/' + INDEX_FILE_NAME
        html += [
            '    <h3 class="header">',
            '    <a href="' + link + '">' + directory + '</a>',
            '    </h3>'
        ]
    # Populate the image gallery table
    # Counter to cycle down through table rows
    table_row_count = 1
    html += ['<hr>', '<table>']
    # For each image file, potentially create a new <tr> and create a new <td>
    for image_file in image_files:
        if table_row_count == 1:
            html.append('<tr>')
        img_src = _get_thumbnail_src_from_file(
            location, image_file, force_no_processing
        )
        link_target = _get_image_link_target_from_file(
            location, image_file, force_no_processing
        )
        html += [
            '    <td>',
            '    <a href="' + link_target + '">',
            '        <img class="image lazyload" src="' + img_src + '">',
            '    </a>',
            '    </td>'
        ]
        if table_row_count == IMAGES_PER_ROW:
            table_row_count = 0
            html.append('</tr>')
        table_row_count += 1
    html += ['</tr>', '</table>']
    html += [
        '    </div>',
        '    </body>',
        '</html>'
    ]
    # Actually create the file, now we've put together the HTML content
    index_file_path = _get_index_file_path(location)
    print('Creating index file %s' % index_file_path)
    index_file = open(index_file_path, 'w')
    index_file.write('\n'.join(html))
    index_file.close()
    # Return the path for cleaning up later
    return index_file_path


def _create_index_files(root_dir, force_no_processing=False):
    """
    Crawl the root directory downwards, generating an index HTML file in each
    directory on the way down.

    @param {String} root_dir - The top level directory to crawl down from. In
        normal usage, this will be '.'.

    @param {Boolean=False} force_no_processing - If True, do not attempt to
        actually process thumbnails, PIL images or anything. Simply index
        <img> tags with original file src attributes.

    @return {[String]} Full file paths of all created files.
    """
    # Initialise list of created file paths to build up as we make them
    created_files = []
    # Walk the root dir downwards, creating index files as we go
    for here, dirs, files in os.walk(root_dir):
        print('Processing %s' % here)
        # Sort the subdirectories by name
        dirs = sorted(dirs)
        # Get image files - all files in the directory matching IMAGE_FILE_REGEX
        image_files = [f for f in files if re.match(IMAGE_FILE_REGEX, f)]
        # Sort the image files by name
        image_files = sorted(image_files)
        # Create this directory's index file and add its name to the created
        # files list
        created_files.append(
            _create_index_file(
                root_dir, here, image_files, dirs, force_no_processing
            )
        )
    # Return the list of created files
    return created_files


def _get_image_from_file(dir_path, image_file):
    """
    Get an instance of PIL.Image from the given file.

    @param {String} dir_path - The directory containing the image file

    @param {String} image_file - The filename of the image file within dir_path

    @return {PIL.Image} An instance of the image file as a PIL Image, or None
        if the functionality is not available. This could be because PIL is not
        present, or because it can't process the given file type.
    """
    # Save ourselves the effort if PIL is not present, and return None now
    if not PIL_ENABLED:
        return None
    # Put together full path
    path = os.path.join(dir_path, image_file)
    # Try to read the image
    img = None
    try:
        img = Image.open(path)
    except IOError as exptn:
        print('Error loading image file %s: %s' % (path, exptn))
    # Return image or None
    return img


def _get_image_link_target_from_file(dir_path, image_file, force_no_processing=False):
    """
    Get the value to be used as the href for links from thumbnail images. For
    most image formats this will simply be the image file name itself. However,
    some image formats (tif) are not natively displayable by many browsers and
    therefore we must link to image data in another format.

    @param {String} dir_path - The directory containing the image file

    @param {String} image_file - The filename of the image file within dir_path

    @param {Boolean=False} force_no_processing - If True, do not attempt to
        actually process a thumbnail, PIL image or anything. Simply return the
        image filename as src.

    @return {String} The href to use.
    """
    # If we've specified to force no processing, just return the image filename
    if force_no_processing:
        return image_file
    # First try to get an image
    img = _get_image_from_file(dir_path, image_file)
    # If format is directly displayable in-browser, just return the filename
    # Else, we need to return a full-sized chunk of displayable image data
    if img.format.lower() in ['tif', 'tiff']:
        return _get_image_src_from_file(
            dir_path, image_file, force_no_processing
        )
    return image_file


def _get_image_src_from_file(dir_path, image_file, force_no_processing=False):
    """
    Get base-64 encoded data as a string for the given image file's full image,
    for use directly in HTML <img> tags, or a path to the original if image
    scaling is not supported.

    This is a full-sized version of _get_thumbnail_src_from_file, for use in
    image formats which cannot be displayed directly in-browser, and therefore
    need processed versions even at full size.

    @param {String} dir_path - The directory containing the image file

    @param {String} image_file - The filename of the image file within dir_path

    @param {Boolean=False} force_no_processing - If True, do not attempt to
        actually process a thumbnail, PIL image or anything. Simply return the
        image filename as src.

    @return {String} The base-64 encoded image data string, or path to the file
        itself if not supported.
    """
    # If we've specified to force no processing, just return the image filename
    if force_no_processing:
        if image_file.endswith('tif') or image_file.endswith('tiff'):
            return UNSUPPORTED_IMAGE_TYPE_DATA
        return image_file
    # First try to get an image
    img = _get_image_from_file(dir_path, image_file)
    return _get_src_from_image(img, image_file)


def _get_index_file_path(location):
    """
    Get the full file path to be used for an index file in the given location.
    Yields location plus the constant INDEX_FILE_NAME.

    @param {String} location - A directory location in which we want to create
        a new index file.

    @return {String} A file path for usage with a new index file.
    """
    return os.path.join(location, INDEX_FILE_NAME)


def _get_server_port():
    """
    Get the port specified for the server to run on. If given as the first
    command line argument, we'll use that. Else we'll default to 8000.

    @return {Integer} The port to run the server on. Default 8000, overridden
        by first command line argument.
    """
    return int(sys.argv[1]) if len(sys.argv) >= 2 else 8000


def _get_src_from_image(img, fallback_image_file):
    """
    Get base-64 encoded data as a string for the given image. Fallback to return
    fallback_image_file if cannot get the image data or img is None.

    @param {Image} img - The PIL Image to get src data for

    @param {String} fallback_image_file - The filename of the image file,
        to be used when image data capture fails

    @return {String} The base-64 encoded image data string, or path to the file
        itself if not supported.
    """
    # If the image is None, then we can't process, so we should return the
    # path to the file itself
    if img is None:
        return fallback_image_file
    # Target format should be the same as the original image format, unless it's
    # a TIF/TIFF, which can't be displayed by most browsers; we convert these
    # to jpeg
    target_format = img.format
    if target_format.lower() in ['tif', 'tiff']:
        target_format = 'JPEG'
    # If we have an actual Image, great - put together the base64 image string
    try:
        bytesio = io.BytesIO()
        img.save(bytesio, target_format)
        byte_value = bytesio.getvalue()
        b64 = base64.b64encode(byte_value)
        return 'data:image/%s;base64,%s' % (target_format.lower(), b64)
    except IOError as exptn:
        print('IOError while saving image bytes: %s' % exptn)
        return fallback_image_file


def _get_thumbnail_image_from_file(dir_path, image_file):
    """
    Get a PIL.Image from the given image file which has been scaled down to
    THUMBNAIL_WIDTH wide.

    @param {String} dir_path - The directory containing the image file

    @param {String} image_file - The filename of the image file within dir_path

    @return {PIL.Image} An instance of the thumbnail as a PIL Image, or None
        if the functionality is not available. See _get_image_from_file for
        details.
    """
    # Get image
    img = _get_image_from_file(dir_path, image_file)
    # If it's not supported, exit now
    if img is None:
        return None
    if img.format.lower() == 'gif':
        return None
    # Get image dimensions
    img_width, img_height = img.size
    # We need to perform a resize - first, work out the scale ratio to take the
    # image width to THUMBNAIL_WIDTH (THUMBNAIL_WIDTH:img_width ratio)
    scale_ratio = THUMBNAIL_WIDTH / float(img_width)
    # Work out target image height based on the scale ratio
    target_height = int(scale_ratio * img_height)
    # Perform the resize
    try:
        img.thumbnail((THUMBNAIL_WIDTH, target_height), resample=RESAMPLE)
    except IOError as exptn:
        print('WARNING: IOError when thumbnailing %s/%s: %s' % (
            dir_path, image_file, exptn
        ))
        return None
    # Return the resized image
    return img


def _get_thumbnail_src_from_file(dir_path, image_file, force_no_processing=False):
    """
    Get base-64 encoded data as a string for the given image file's thumbnail,
    for use directly in HTML <img> tags, or a path to the original if image
    scaling is not supported.

    @param {String} dir_path - The directory containing the image file

    @param {String} image_file - The filename of the image file within dir_path

    @param {Boolean=False} force_no_processing - If True, do not attempt to
        actually process a thumbnail, PIL image or anything. Simply return the
        image filename as src.

    @return {String} The base-64 encoded image data string, or path to the file
        itself if not supported.
    """
    # If we've specified to force no processing, just return the image filename
    if force_no_processing:
        if image_file.endswith('tif') or image_file.endswith('tiff'):
            return UNSUPPORTED_IMAGE_TYPE_DATA
        return image_file
    # First try to get a thumbnail image
    img = _get_thumbnail_image_from_file(dir_path, image_file)
    return _get_src_from_image(img, image_file)


def _run_server():
    """
    Run the image server. This is blocking. Will handle user KeyboardInterrupt
    and other exceptions appropriately and return control once the server is
    stopped.

    @return {None}
    """
    # Get the port to run on
    port = _get_server_port()
    # Configure allow_reuse_address to make re-runs of the script less painful -
    # if this is not True then waiting for the address to be freed after the
    # last run can block a subsequent run
    # SocketServer.TCPServer.allow_reuse_address = True
    socketserver.TCPServer.allow_reuse_address = True
    # Create the server instance
    server = socketserver.TCPServer(
        ('', port),
        # SimpleHTTPServer.SimpleHTTPRequestHandler,
        http.server.SimpleHTTPRequestHandler
    )
    # Print out before actually running the server (cheeky / optimistic, however
    # you want to look at it)
    print('Your images are at http://127.0.0.1:%d/%s' % (
        port,
        INDEX_FILE_NAME
    ))
    # Try to run the server
    try:
        # Run it - this call blocks until the server is killed
        server.serve_forever()
    except KeyboardInterrupt:
        # This is the expected way of the server being killed, since imageMe is
        # intended for ad-hoc running from command line
        print('User interrupted, stopping')
    except Exception as exptn:
        # Catch everything else - this will handle shutdowns via other signals
        # and faults actually starting the server in the first place
        print(exptn)
        print('Unhandled exception in server, stopping')


def serve_dir(dir_path):
    """
    Generate indexes and run server from the given directory downwards.

    @param {String} dir_path - The directory path (absolute, or relative to CWD)

    @return {None}
    """
    # Create index files, and store the list of their paths for cleanup later
    # This time, force no processing - this gives us a fast first-pass in terms
    # of page generation, but potentially slow serving for large image files
    print('Performing first pass index file generation')
    created_files = _create_index_files(dir_path, True)
    if (PIL_ENABLED):
        # If PIL is enabled, we'd like to process the HTML indexes to include
        # generated thumbnails - this slows down generation so we don't do it
        # first time around, but now we're serving it's good to do in the
        # background
        print('Performing PIL-enchanced optimised index file generation in background')
        background_indexer = BackgroundIndexFileGenerator(dir_path)
        background_indexer.run()
    # Run the server in the current location - this blocks until it's stopped
    _run_server()
    # Clean up the index files created earlier so we don't make a mess of
    # the image directories
    _clean_up(created_files)


if __name__ == '__main__':
    # Generate indices and serve from the current directory downwards when run
    # as the entry point
    serve_dir('.')
