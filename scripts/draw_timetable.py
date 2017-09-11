import os
import _mysql
import sys
import datetime





def colorstr(rgb): return "#%02x%02x%02x" % (rgb[0],rgb[1],rgb[2])


def hsl_to_rgb(h, s, l):
    c = (1 - abs(2*l - 1)) * s
    x = c * (1 - abs(h *1.0 / 60 % 2 - 1))
    m = l - c/2
    if h < 60:
        r, g, b = c + m, x + m, 0 + m
    elif h < 120:
        r, g, b = x + m, c+ m, 0 + m
    elif h < 180:
        r, g, b = 0 + m, c + m, x + m
    elif h < 240:
        r, g, b, = 0 + m, x + m, c + m
    elif h < 300:
        r, g, b, = x + m, 0 + m, c + m
    else:
        r, g, b, = c + m, 0 + m, x + m
    r = int(r * 255)
    g = int(g * 255)
    b = int(b * 255)
    return (r,g,b)

class scalableVectorGraphics:

    def __init__(self, height, width):
        self.height = height
        self.width = width
        self.out = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg
   xmlns:dc="http://purl.org/dc/elements/1.1/"
   xmlns:cc="http://creativecommons.org/ns#"
   xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
   xmlns:svg="http://www.w3.org/2000/svg"
   xmlns="http://www.w3.org/2000/svg"
   xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
   xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
   height="%d"
   width="%d"
   id="svg2"
   version="1.1"
   inkscape:version="0.48.4 r9939"
   sodipodi:docname="easyfig">
  <metadata
     id="metadata122">
    <rdf:RDF>
      <cc:Work
         rdf:about="">
        <dc:format>image/svg+xml</dc:format>
        <dc:type
           rdf:resource="http://purl.org/dc/dcmitype/StillImage" />
        <dc:title>Easyfig</dc:title>
      </cc:Work>
    </rdf:RDF>
  </metadata>
  <defs
     id="defs120" />
  <sodipodi:namedview
     pagecolor="#ffffff"
     bordercolor="#666666"
     borderopacity="1"
     objecttolerance="10"
     gridtolerance="10"
     guidetolerance="10"
     inkscape:pageopacity="0"
     inkscape:pageshadow="2"
     inkscape:window-width="640"
     inkscape:window-height="480"
     id="namedview118"
     showgrid="false"
     inkscape:zoom="0.0584"
     inkscape:cx="2500"
     inkscape:cy="75.5"
     inkscape:window-x="55"
     inkscape:window-y="34"
     inkscape:window-maximized="0"
     inkscape:current-layer="svg2" />
  <title
     id="title4">Easyfig</title>
  <g
     style="fill-opacity:1.0; stroke:black; stroke-width:1;"
     id="g6">''' % (self.height, self.width)

    def change_height(self, new_height):
        self.out = self.out.replace('height="' + str(self.height) + '"', 'height="' + str(new_height) + '"', 1)
  
    def drawLine(self, x1, y1, x2, y2, th=1, cl=(0, 0, 0), alpha = 1.0):
        self.out += '  <line x1="%d" y1="%d" x2="%d" y2="%d"\n        stroke-width="%d" stroke="%s" stroke-opacity="%f" stroke-linecap="butt" />\n' % (x1, y1, x2, y2, th, colorstr(cl), alpha)

    def drawPath(self, xcoords, ycoords, th=1, cl=(0, 0, 0), alpha=0.9):
        self.out += '  <path d="M%d %d' % (xcoords[0], ycoords[0])
        for i in range(1, len(xcoords)):
            self.out += ' L%d %d' % (xcoords[i], ycoords[i])
        self.out += '"\n        stroke-width="%d" stroke="%s" stroke-opacity="%f" stroke-linecap="butt" fill="none" z="-1" />\n' % (th, colorstr(cl), alpha)


    def writesvg(self, filename):
        outfile = open(filename, 'w')
        outfile.write(self.out + ' </g>\n</svg>')
        outfile.close()

    def drawRightArrow(self, x, y, wid, ht, fc, oc=(0,0,0), lt=1):
        if lt > ht /2:
            lt = ht/2
        x1 = x + wid
        y1 = y + ht/2
        x2 = x + wid - ht / 2
        ht -= 1
        if wid > ht/2:
            self.out += '  <polygon fill="%s" stroke="%s" stroke-width="%d"\n' % (colorstr(fc), colorstr(oc), lt)
            self.out += '           points="%d,%d %d,%d %d,%d %d,%d %d,%d %d,%d %d,%d" />\n' % (x, y+ht/4, x2, y+ht/4,
                                                                                                x2, y, x1, y1, x2, y+ht,
                                                                                                x2, y+3*ht/4, x, y+3*ht/4)
        else:
            self.out += '  <polygon fill="%s" stroke="%s" stroke-width="%d"\n' % (colorstr(fc), colorstr(oc), lt)
            self.out += '           points="%d,%d %d,%d %d,%d" />\n' % (x, y, x, y+ht, x + wid, y1)

    def drawLeftArrow(self, x, y, wid, ht, fc, oc=(0,0,0), lt=1):
        if lt > ht /2:
            lt = ht/2
        x1 = x + wid
        y1 = y + ht/2
        x2 = x + ht / 2
        ht -= 1
        if wid > ht/2:
            self.out += '  <polygon fill="%s" stroke="%s" stroke-width="%d"\n' % (colorstr(fc), colorstr(oc), lt)
            self.out += '           points="%d,%d %d,%d %d,%d %d,%d %d,%d %d,%d %d,%d" />\n' % (x1, y+ht/4, x2, y+ht/4,
                                                                                                x2, y, x, y1, x2, y+ht,
                                                                                                x2, y+3*ht/4, x1, y+3*ht/4)
        else:
            self.out += '  <polygon fill="%s" stroke="%s" stroke-width="%d"\n' % (colorstr(fc), colorstr(oc), lt)
            self.out += '           points="%d,%d %d,%d %d,%d" />\n' % (x, y1, x1, y+ht, x1, y)

    def drawBlastHit(self, x1, y1, x2, y2, x3, y3, x4, y4, fill=(0, 0, 255), lt=2, alpha=0.1):
        self.out += '  <polygon fill="%s" stroke="%s" stroke-width="%d" fill-opacity="%f"\n' % (colorstr(fill), colorstr((0,0,0)), lt, alpha)
        self.out += '           points="%d,%d %d,%d %d,%d %d,%d" />\n' % (x1, y1, x2, y2, x3, y3, x4, y4)

    def drawGradient(self, x1, y1, wid, hei, minc, maxc):
        self.out += '  <defs>\n    <linearGradient id="MyGradient" x1="0%" y1="0%" x2="0%" y2="100%">\n'
        self.out += '      <stop offset="0%%" stop-color="%s" />\n' % colorstr(maxc)
        self.out += '      <stop offset="100%%" stop-color="%s" />\n' % colorstr(minc)
        self.out += '    </linearGradient>\n  </defs>\n'
        self.out += '  <rect fill="url(#MyGradient)" stroke-width="0"\n'
        self.out += '        x="%d" y="%d" width="%d" height="%d"/>\n' % (x1, y1, wid, hei)

    def drawGradient2(self, x1, y1, wid, hei, minc, maxc):
        self.out += '  <defs>\n    <linearGradient id="MyGradient2" x1="0%" y1="0%" x2="0%" y2="100%">\n'
        self.out += '      <stop offset="0%%" stop-color="%s" />\n' % colorstr(maxc)
        self.out += '      <stop offset="100%%" stop-color="%s" />\n' % colorstr(minc)
        self.out += '    </linearGradient>\n</defs>\n'
        self.out += '  <rect fill="url(#MyGradient2)" stroke-width="0"\n'
        self.out += '        x="%d" y="%d" width="%d" height="%d" />\n' % (x1, y1, wid, hei)

    def drawOutRect(self, x1, y1, wid, hei, fill=(255, 255, 255), outfill=(0, 0, 0), lt=1, alpha=1.0, alpha2=1.0):
        self.out += '  <rect stroke="%s" stroke-width="%d" stroke-opacity="%f"\n' % (colorstr(outfill), lt, alpha)
        self.out += '        fill="%s" fill-opacity="%f"\n' % (colorstr(fill), alpha2)
        self.out += '        x="%d" y="%d" width="%d" height="%d" />\n' % (x1, y1, wid, hei)

    def drawAlignment(self, x, y, fill, outfill, lt=1, alpha=1.0, alpha2=1.0):
        self.out += '  <polygon fill="%s" stroke="%s" stroke-width="%d" stroke-opacity="%f" fill-opacity="%f"\n' % (colorstr(fill), outfill, lt, alpha, alpha2)
        self.out += '  points="'
        for i, j in zip(x, y):
            self.out += str(i) + ',' + str(j) + ' '
        self.out += '" />\n'
             # print self.out.split('\n')[-2]



    def drawSymbol(self, x, y, size, fill, symbol, alpha=1.0, lt=1):
        x0 = x - size/2
        x1 = size/8 + x - size/2
        x2 = size/4 + x - size/2
        x3 = size*3/8 + x - size/2
        x4 = size/2 + x - size/2
        x5 = size*5/8 + x - size/2
        x6 = size*3/4 + x - size/2
        x7 = size*7/8 + x - size/2
        x8 = size + x - size/2
        y0 = y - size/2
        y1 = size/8 + y - size/2
        y2 = size/4 + y - size/2
        y3 = size*3/8 + y - size/2
        y4 = size/2 + y - size/2
        y5 = size*5/8 + y - size/2
        y6 = size*3/4 + y - size/2
        y7 = size*7/8 + y - size/2
        y8 = size + y - size/2
        if symbol == 'o':
            self.out += '  <circle stroke="%s" stroke-width="%d" stroke-opacity="%f"\n' % (colorstr((0, 0, 0)), lt, alpha)
            self.out += '        fill="%s" fill-opacity="%f"\n' % (colorstr(fill), alpha)
            self.out += '        cx="%d" cy="%d" r="%d" />\n' % (x, y, size/2)
        elif symbol == 'x':
            self.out += '  <polygon fill="%s" stroke="%s" stroke-width="%d" stroke-opacity="%f" fill-opacity="%f"\n' % (colorstr(fill), colorstr((0, 0, 0)), lt, alpha, alpha)
            self.out += '           points="%d,%d %d,%d %d,%d %d,%d %d,%d %d,%d %d,%d %d,%d %d,%d %d,%d %d,%d %d,%d" />\n' % (x0, y2, x2, y0, x4, y2, x6, y0, x8, y2,
                                                                                                                             x6, y4, x8, y6, x6, y8, x4, y6, x2, y8,
                                                                                                                             x0, y6, x2, y4)
        elif symbol == '+':
            self.out += '  <polygon fill="%s" stroke="%s" stroke-width="%d" stroke-opacity="%f" fill-opacity="%f"\n' % (colorstr(fill), colorstr((0, 0, 0)), lt, alpha, alpha)
            self.out += '           points="%d,%d %d,%d %d,%d %d,%d %d,%d %d,%d %d,%d %d,%d %d,%d %d,%d %d,%d %d,%d" />\n' % (x2, y0, x6, y0, x6, y2, x8, y2, x8, y6,
                                                                                                                             x6, y6, x6, y8, x2, y8, x2, y6, x0, y6,
                                                                                                                             x0, y2, x2, y2)
        elif symbol == 's':
            self.out += '  <polygon fill="%s" stroke="%s" stroke-width="%d" stroke-opacity="%f" fill-opacity="%f"\n' % (colorstr(fill), colorstr((0, 0, 0)), lt, alpha, alpha)
            self.out += '           points="%d,%d %d,%d %d,%d %d,%d" />\n' % (x0, y0, x0, y8, x8, y8, x8, y0)
        elif symbol == '^':
            self.out += '  <polygon fill="%s" stroke="%s" stroke-width="%d" stroke-opacity="%f" fill-opacity="%f"\n' % (colorstr(fill), colorstr((0, 0, 0)), lt, alpha, alpha)
            self.out += '           points="%d,%d %d,%d %d,%d %d,%d %d,%d %d,%d" />\n' % (x0, y0, x2, y0, x4, y4, x6, y0, x8, y0, x4, y8)
        elif symbol == 'v':
            self.out += '  <polygon fill="%s" stroke="%s" stroke-width="%d" stroke-opacity="%f" fill-opacity="%f"\n' % (colorstr(fill), colorstr((0, 0, 0)), lt, alpha, alpha)
            self.out += '           points="%d,%d %d,%d %d,%d %d,%d %d,%d %d,%d" />\n' % (x0, y8, x2, y8, x4, y4, x6, y8, x8, y8, x4, y0)
        elif symbol == 'u':
            self.out += '  <polygon fill="%s" stroke="%s" stroke-width="%d" stroke-opacity="%f" fill-opacity="%f"\n' % (colorstr(fill), colorstr((0, 0, 0)), lt, alpha, alpha)
            self.out += '           points="%d,%d %d,%d %d,%d" />\n' % (x0, y8, x4, y0, x8, y8)
        elif symbol == 'd':
            self.out += '  <polygon fill="%s" stroke="%s" stroke-width="%d" stroke-opacity="%f" fill-opacity="%f"\n' % (colorstr(fill), colorstr((0, 0, 0)), lt, alpha, alpha)
            self.out += '           points="%d,%d %d,%d %d,%d" />\n' % (x0, y0, x4, y8, x8, y0)
        else:
            sys.stderr.write(symbol + '\n')
            sys.stderr.write('Symbol not found, this should not happen.. exiting')
            sys.exit()








    def drawRightFrame(self, x, y, wid, ht, lt, frame, fill):
        if lt > ht /2:
            lt = ht /2
        if frame == 1:
            y1 = y + ht/2
            y2 = y + ht * 3/8
            y3 = y + ht * 1/4
        elif frame == 2:
            y1 = y + ht * 3/8
            y2 = y + ht * 1/4
            y3 = y + ht * 1/8
        elif frame == 0:
            y1 = y + ht * 1/4
            y2 = y + ht * 1/8
            y3 = y + 1
        x1 = x
        x2 = x + wid - ht/8
        x3 = x + wid
        if wid > ht/8:
            self.out += '  <polygon fill="%s" stroke="%s" stroke-width="%d"\n' % (colorstr(fill), colorstr((0, 0, 0)), lt)
            self.out += '           points="%d,%d %d,%d %d,%d %d,%d %d,%d" />\n' % (x1, y1, x2, y1, x3, y2, x2, y3, x1, y3)
        else:
            self.out += '  <polygon fill="%s" stroke="%s" stroke-width="%d"\n' % (colorstr(fill), colorstr((0, 0, 0)), lt)
            self.out += '           points="%d,%d %d,%d %d,%d" />\n' % (x1, y1, x3, y2, x1, y3)

    def drawRightFrameRect(self, x, y, wid, ht, lt, frame, fill):
        if lt > ht /2:
            lt = ht /2
        if frame == 1:
            y1 = y + ht / 4
        elif frame == 2:
            y1 = y + ht /8
        elif frame == 0:
            y1 = y + 1
        hei = ht /4
        x1 = x
        self.out += '  <rect fill="%s" stroke-width="%d"\n' % (colorstr(fill), lt)
        self.out += '        x="%d" y="%d" width="%d" height="%d" />\n' % (x1, y1, wid, hei)

    def drawLeftFrame(self, x, y, wid, ht, lt, frame, fill):
        if lt > ht /2:
            lt = ht /2
        if frame == 1:
            y1 = y + ht
            y2 = y + ht * 7/8
            y3 = y + ht * 3/4
        elif frame == 2:
            y1 = y + ht * 7/8
            y2 = y + ht * 3/4
            y3 = y + ht * 5/8
        elif frame == 0:
            y1 = y + ht * 3/4
            y2 = y + ht * 5/8
            y3 = y + ht / 2
        x1 = x + wid
        x2 = x + ht/8
        x3 = x
        if wid > ht/8:
            self.out += '  <polygon fill="%s" stroke="%s" stroke-width="%d"\n' % (colorstr(fill), colorstr((0, 0, 0)), lt)
            self.out += '           points="%d,%d %d,%d %d,%d %d,%d %d,%d" />\n' % (x1, y1, x2, y1, x3, y2, x2, y3, x1, y3)
        else:
            self.out += '  <polygon fill="%s" stroke="%s" stroke-width="%d"\n' % (colorstr(fill), colorstr((0, 0, 0)), lt)
            self.out += '           points="%d,%d %d,%d %d,%d" />\n' % (x1, y1, x3, y2, x1, y3)

    def drawLeftFrameRect(self, x, y, wid, ht, lt, frame, fill):
        if lt > ht /2:
            lt = ht /2
        if frame == 1:
            y1 = y + ht * 3/4
        elif frame == 2:
            y1 = y + ht * 5/8
        elif frame == 0:
            y1 = y + ht / 2
        hei = ht /4
        x1 = x
        self.out += '  <rect fill="%s" stroke-width="%d"\n' % (colorstr(fill), lt)
        self.out += '        x="%d" y="%d" width="%d" height="%d" />\n' % (x1, y1, wid, hei)

    def drawPointer(self, x, y, ht, lt, fill):
        x1 = x - int(round(0.577350269 * ht/2))
        x2 = x + int(round(0.577350269 * ht/2))
        y1 = y + ht/2
        y2 = y + 1
        self.out += '  <polygon fill="%s" stroke="%s" stroke-width="%d"\n' % (colorstr(fill), colorstr((0, 0, 0)), lt)
        self.out += '           points="%d,%d %d,%d %d,%d" />\n' % (x1, y2, x2, y2, x, y1)

    def drawDash(self, x1, y1, x2, y2, exont):
        self.out += '  <line x1="%d" y1="%d" x2="%d" y2="%d"\n' % (x1, y1, x2, y2)
        self.out += '       style="stroke-dasharray: 5, 3, 9, 3"\n'
        self.out += '       stroke="#000" stroke-width="%d" />\n' % exont

    def drawPolygon(self, x_coords, y_coords, colour=(0,0,255)):
        self.out += '  <polygon points="'
        for i,j in zip(x_coords, y_coords):
            self.out += str(i) + ',' + str(j) + ' '
        self.out += '"\nstyle="fill:%s;stroke=none" />\n'  % colorstr(colour)
    def writeString(self, thestring, x, y, size, ital=False, bold=False, rotate=0, justify='left'):
        if rotate != 0:
            x, y = y, x
        self.out += '  <text\n'
        self.out += '    style="font-size:%dpx;font-style:normal;font-weight:normal;z-index:10\
;line-height:125%%;letter-spacing:0px;word-spacing:0px;fill:#111111;fill-opacity:1;stroke:none;font-family:Sans"\n' % size
        if justify == 'right':
            self.out += '    text-anchor="end"\n'
        elif justify == 'middle':
            self.out += '    text-anchor="middle"\n'
        if rotate == 1:
            self.out += '    x="-%d"\n' % x
        else:
            self.out += '    x="%d"\n' % x
        if rotate == -1:
            self.out += '    y="-%d"\n' % y
        else:
            self.out += '    y="%d"\n' % y
        self.out += '    sodipodi:linespacing="125%"'
        if rotate == -1:
            self.out += '\n    transform="matrix(0,1,-1,0,0,0)"'
        if rotate == 1:
            self.out += '\n    transform="matrix(0,-1,1,0,0,0)"'
        self.out += '><tspan\n      sodipodi:role="line"\n'
        if rotate == 1:
            self.out += '      x="-%d"\n' % x
        else:
            self.out += '      x="%d"\n' % x
        if rotate == -1:
            self.out += '      y="-%d"' % y
        else:
            self.out += '      y="%d"' % y
        if ital and bold:
            self.out += '\nstyle="font-style:italic;font-weight:bold"'
        elif ital:
            self.out += '\nstyle="font-style:italic"'
        elif bold:
            self.out += '\nstyle="font-style:normal;font-weight:bold"'
        self.out += '>' + thestring + '</tspan></text>\n'




def get_time(astring):
    if astring == '':
        return None
    elif ' ' in astring:
        date, time = astring.split()
        hour, minute, second = time.split(':')
    else:
        date = astring
        hour, minute, second = 12, 0, 0
    if '-' in date:
        year, month, day = date.split('-')
    else:
        month, day, year = date.split('/')
    month, day, year, hour, minute, second = map(int, [month, day, year, hour, minute, second])
    return datetime.datetime(year, month, day, hour, minute, second)

def get_x_time(time, start_time, end_time, width):
    totalsecs = (end_time-start_time).total_seconds()
    time_to_event = (time-start_time).total_seconds()
    return time_to_event / totalsecs * width


class patient:
    def __init__(self, erap):
        self.erap = erap
        self.isolates = []
        self.encounters = []
        self.procedures = []
        self.specimens = []
        self.antibiotics = {}


def draw_timeline(patients, outfile, start_time, end_time, isolate_list):
    color_list = [(240,163,255),(0,117,220),(153,63,0),(76,0,92),(25,25,25),(0,92,49),(43,206,72),(255,204,153),
                  (128,128,128),(148,255,181),(143,124,0),(157,204,0),(194,0,136),(0,51,128),(255,164,5),(255,168,187),
                  (66,102,0),(255,0,16),(94,241,242),(0,153,143),(224,255,102),(116,10,255),(153,0,0),(255,255,128),
                  (255,255,0),(255,80,5), (0, 0, 0), (50, 50, 50)]
    loc_color = {}
    ab_color = {}
    ab_color_index = 0
    proc_color = {}
    proc_color_index = 0
    color_index = 0
    left_buffer = 500
    top_buffer = 1000
    bot_buffer = 100
    right_buffer = 1000
    width = 5000
    pat_height = 80
    stay_height = 20
    isolate_height = 40
    font_size = 36
    ab_height = 12
    svg = scalableVectorGraphics(len(patients) * pat_height + top_buffer + bot_buffer, width + left_buffer + right_buffer)
    start_dt, end_dt = start_time, end_time
    first_tick = start_dt - datetime.timedelta(hours=start_dt.hour, minutes=start_dt.minute, seconds=start_dt.second)
    first_tick += datetime.timedelta(hours=24)
    extract_list = []
    firstday = datetime.datetime(2014, 9, 1)
    sample_type_symbol = {'query isolate':'x',
                          'SW':'s',
                          'CD':'+',
                          'RC':'o',
                          'ER':'u',
                          'PS':'d'}
    cd_tox_color = {'CD-Pos TOX-Pos':(106,202,143),
                    'CD-Pos TOX-Neg':(217,121,196),
                    'CD-Neg TOX-Pos':(113,202,87),
                    'CD-Neg TOX-Neg':(127,149,227),
                    'Positive':(185,191,88),
                    'Negative':(230,112,101),
                    'Inconclusive':(80,206,208),
                    'none':(210,148,73)}
    for num, i in enumerate(patients):
        if num % 2 == 0:
            svg.drawOutRect(left_buffer, num * pat_height + top_buffer, width, pat_height, fill=(220, 220, 220), lt=0)
    count = 0
    while first_tick < end_dt:
        count += 1
        x = get_x_time(first_tick, start_dt, end_dt, width)
        if count % 5 == 0:
            the_delta = first_tick - firstday
            svg.drawLine(left_buffer + x, top_buffer, left_buffer + x, len(patients) * pat_height + top_buffer, th=3)
            svg.writeString('Day ' + str(the_delta.days), left_buffer + x, top_buffer - 10, font_size, rotate=-1,justify='right')
            # svg.writeString(first_tick.isoformat()[:10], left_buffer + x, top_buffer - 10, font_size, rotate=-1,justify='right')
        else:
            svg.drawLine(left_buffer + x, top_buffer, left_buffer + x, len(extract_list) * pat_height + top_buffer, th=2)
        first_tick += datetime.timedelta(hours=24*7)
    for num, i in enumerate(patients):
        svg.writeString(i.erap, left_buffer - 5, num * pat_height + pat_height/2 + font_size/3 + top_buffer, font_size, justify='right')
        for j in i.encounters:
            start, end, loc = j
            start = get_time(start)
            end = get_time(end)
            startx = get_x_time(start, start_dt, end_dt, width)
            endx = get_x_time(end, start_dt, end_dt, width)
            if not loc in loc_color:
                loc_color[loc] = color_list[color_index]
                color_index = (color_index + 1) % len(color_list)
            color = loc_color[loc]
            if start_dt <= start <= end <= end_dt:
                svg.drawOutRect(startx + left_buffer, num * pat_height + top_buffer + (pat_height - stay_height) / 2, endx - startx, stay_height, fill=color, lt=0)
        for j in i.specimens:
            time = get_time(j[1])
            if start_dt <= time <= end_dt:
                x = get_x_time(time, start_dt, end_dt, width)
                if j[0] in isolate_list:
                    symbol = sample_type_symbol['query isolate']
                else:
                    symbol = sample_type_symbol[j[0][:2]]
                color = cd_tox_color[j[2]]
                svg.drawSymbol(x + left_buffer, top_buffer + num * pat_height + pat_height/2 + stay_height/2 + isolate_height/4, isolate_height/2, color, symbol)
        for j in i.isolates:
            time = get_time(j[1])
            if start_dt <= time <= end_dt:
                x = get_x_time(time, start_dt, end_dt, width)
                if j[0] in isolate_list:
                    symbol = sample_type_symbol['query isolate']
                else:
                    symbol = sample_type_symbol[j[0][:2]]
                color = cd_tox_color[j[2]]
                svg.drawSymbol(x + left_buffer, top_buffer +  num * pat_height + pat_height/2, isolate_height, color, symbol)
        for j in i.procedures:
            time = get_time(j[0])
            procedure = j[1]
            if procedure in proc_color:
                color = proc_color[procedure]
            else:
                color = color_list[proc_color_index]
                proc_color[procedure] = color
                proc_color_index = (proc_color_index+1) % len(color_list)
            x = get_x_time(time, start_dt, end_dt, width)
            svg.drawSymbol(x + left_buffer, top_buffer + num * pat_height + 3 * pat_height/4, ab_height, color, 'u')
        taken = [[]]
        ab_y = top_buffer +  num * pat_height + pat_height/4
        for j in i.antibiotics:
            i.antibiotics[j].sort(key=lambda x:x[0]-x[1])
            if j in ab_color:
                color = ab_color[j]
            else:
                color = color_list[ab_color_index]
                ab_color[j] = color
                ab_color_index = (ab_color_index+1) % len(color_list)
            for k in i.antibiotics[j]:
                x1 = get_x_time(k[0], start_dt, end_dt, width)
                x2 = get_x_time(k[1], start_dt, end_dt, width)
                if x1 != x2:
                    y_row = None
                    for num2, j in enumerate(taken):
                        this_y = True
                        for k in j:
                            if x1 <= k[0] and x2 >= k[0] or x1 <= k[1] and x2 >= k[1]:
                                this_y = False
                                break
                        if this_y:
                            y_row = num2
                            j.append((x1, x2))
                            break
                    if y_row is None:
                        taken.append([(x1, x2)])
                        y_row = len(taken) - 1
                    svg.drawLine(x1 + left_buffer, ab_y + y_row * 1.1 * ab_height, x2 + left_buffer,
                                 ab_y + y_row * 1.1 * ab_height, th=ab_height, cl=color)
                else:
                    svg.drawSymbol(x1 + left_buffer, ab_y, ab_height, color, 'x')
    leg_start = len(patients) * pat_height + top_buffer + bot_buffer
    max_y = 0
    for num, i in enumerate(loc_color):
        svg.drawOutRect(left_buffer, leg_start + pat_height * num, stay_height * 2, stay_height, fill=loc_color[i], lt=0)
        svg.writeString(i, left_buffer + stay_height * 2 + 10, leg_start + pat_height * num + stay_height, font_size)
        if leg_start + pat_height * num + stay_height >= max_y:
            max_y = leg_start + pat_height * num + stay_height
    for num, i in enumerate(ab_color):
        svg.drawOutRect(left_buffer + width/5, leg_start + pat_height * num, stay_height * 2, stay_height, fill=ab_color[i], lt=0)
        svg.writeString(i, left_buffer + width/5 + stay_height * 2 + 10, leg_start + pat_height * num + stay_height, font_size)
        if leg_start + pat_height * num + stay_height >= max_y:
            max_y = leg_start + pat_height * num + stay_height
    for num, i in enumerate(cd_tox_color):
        svg.drawOutRect(left_buffer + width*2/5, leg_start + pat_height * num, stay_height * 2, stay_height, fill=cd_tox_color[i], lt=0)
        svg.writeString(i, left_buffer + width*2/5 + stay_height * 2 + 10, leg_start + pat_height * num + stay_height, font_size)
        if leg_start + pat_height * num + stay_height >= max_y:
            max_y = leg_start + pat_height * num + stay_height
    for num, i in enumerate(sample_type_symbol):
        svg.drawSymbol(left_buffer + width*3/5 + stay_height/2, leg_start + pat_height * num, stay_height, (200, 200, 200), sample_type_symbol[i])
        svg.writeString(i, left_buffer + width*3/5 + stay_height * 2 + 10, leg_start + pat_height * num + stay_height, font_size)
        if leg_start + pat_height * num + stay_height >= max_y:
            max_y = leg_start + pat_height * num + stay_height
    for num, i in enumerate(proc_color):
        svg.drawOutRect(left_buffer + width*4/5, leg_start + pat_height * num, stay_height * 2, stay_height, fill=proc_color[i], lt=0)
        svg.writeString(i, left_buffer + width*4/5 + stay_height * 2 + 10, leg_start + pat_height * num + stay_height, font_size)
        if leg_start + pat_height * num + stay_height >= max_y:
            max_y = leg_start + pat_height * num + stay_height
    print max_y
    svg.change_height(max_y)
    svg.writesvg(outfile)


def get_dates(acc_nos):
    path = os.path.expanduser('~') + '/.my.cnf'
    with open(path) as cnf_file:
        for line in cnf_file:
            if line.startswith('user='):
                user = line.rstrip()[5:]
            if line.startswith('password='):
                pw = line.rstrip()[9:]
            if line.startswith('host='):
                host = line.rstrip()[5:]
            if line.startswith('database='):
                database = line.rstrip()[9:]
    db = _mysql.connect(host=host,user=user,passwd=pw,db=database)
    rejected = []
    out_list = []
    for isolate in acc_nos:
        try:
            db.query("""select eRAP_ID from tIsolates where isolate_ID='""" + isolate + "'")
            val = db.store_result()
            erap = val.fetch_row()[0][0]
            if erap is None:
                continue
            the_patient = patient(erap)
        except IndexError:
            pass
        try:
            db.query("""select isolate_ID, collection_date from tIsolates where eRAP_ID='""" + erap + "'")
            val = db.store_result()
            for isolate_id in val.fetch_row(maxrows=0):
                db.query("""select cdi_test_PCR, cdi_test_quikchek from tCdiffProjectSamples where specimen_ID='""" + isolate_id[0] + "'")
                val2 = db.store_result()
                cdi_results = val2.fetch_row()
                if cdi_results == ():
                    cdi_results = 'none'
                elif cdi_results[0][1] != 'Todo' and cdi_results[0][1] != 'Not planned' and cdi_results[0][1] != 'Not Planned':
                    cdi_results = cdi_results[0][1]
                elif cdi_results[0][0] != 'Todo' and cdi_results[0][0] != 'Not planned' and cdi_results[0][0] != 'Not Planned':
                    cdi_results = cdi_results[0][0]
                else:
                    cdi_results = 'none'
                the_patient.isolates.append(isolate_id + (cdi_results,))
        except IndexError:
            pass
        db.query("""select specimen_ID, collection_date from tStoolCollection where eRAP_ID='""" + erap + "'")
        val = db.store_result()
        for sample_id in val.fetch_row(maxrows=0):
            spec_id = sample_id[0]
            if '.' in spec_id:
                spec_id = spec_id.split('.')[0]
            db.query("""select cdi_test_PCR, cdi_test_quikchek from tCdiffProjectSamples where specimen_ID='""" + spec_id + "'")
            val2 = db.store_result()
            cdi_results = val2.fetch_row()
            if cdi_results == ():
                cdi_results = 'none'
            elif cdi_results[0][1] != 'Todo' and cdi_results[0][1] != 'Not planned' and cdi_results[0][1] != 'Not Planned':
                cdi_results = cdi_results[0][1]
            elif cdi_results[0][0] != 'Todo' and cdi_results[0][0] != 'Not planned' and cdi_results[0][0] != 'Not Planned':
                cdi_results = cdi_results[0][0]
            else:
                cdi_results = 'none'
            the_patient.specimens.append(sample_id + (cdi_results,))
        # try:
        db.query("""select * from tPatientEncounter where eRAP_ID='""" + erap + "'")
        val = db.store_result()
        for row in val.fetch_row(maxrows=0):
            start_date, end_date, unit, visit_type, age, sex, bmi, smoke = row[2:]
            if visit_type == 'Hospital Encounter':
                the_patient.encounters.append((start_date, end_date, unit))
        # except IndexError:
        #     pass

        db.query("""select procedure_date, procedure_ID from tPatientProcedures where eRAP_ID='""" + erap + "'")
        val = db.store_result()
        for proc in val.fetch_row(maxrows=0):
            the_patient.procedures.append(proc)
        db.query("""select administered_date, med_ID, frequency from tPatientAntibiotics where eRAP_ID='""" + erap + "'")
        val = db.store_result()
        ab_dict = {}
        for ab in val.fetch_row(maxrows=0):
            date, ab_id, frequency = ab
            if frequency in set(['WEEKLY', 'EVERY 7 DAYS', 'EVERY WED', 'EVERY TUES; THURS', 'EVERY MON; FRI', 'EVERY WED; SAT', 'DURING DIALYSIS']):
                freq = datetime.timedelta(days=7)
            elif frequency in set(['EVERY OTHER DAY', 'EVERY 2 DAYS', 'EVERY 36 HOURS']):
                freq = datetime.timedelta(days=2)
            elif frequency in set(['EVERY 3 DAYS', 'EVERY TUES; THURS; SAT', 'EVERY MON; WED; FRI', 'POST DIALYSIS (Tues; Thurs; Sat)',
                                   'EVERY 72 HOURS', 'EVERY MON; THURS; SAT', 'POST DIALYSIS (Mon; Wed; Fri)']):
                freq = datetime.timedelta(days=3)
            else:
                freq = datetime.timedelta(days=1)
            if ab_id in ab_dict:
                ab_dict[ab_id].append((get_time(date), freq))
            else:
                ab_dict[ab_id] = [(get_time(date), freq)]
        ab_dates = {}
        for i in ab_dict:
            ab_dates[i] = []
            date_list = ab_dict[i]
            date_list.sort()
            date_range = [date_list[0][0], date_list[0][0]]
            for j in date_list[1:]:
                if date_range[1] + j[1] >= j[0]:
                    date_range[1] = j[0]
                else:
                    ab_dates[i].append(date_range)
                    date_range = [j[0], j[0]]
            ab_dates[i].append(date_range)
        the_patient.antibiotics = ab_dates
        getit = True
        for i in out_list:
            if i.erap == erap:
                getit = False
                break
        if getit:
            out_list.append(the_patient)
    return out_list

def get_isolate_list(filename):
    with open(filename) as f:
        isolates = []
        for line in f:
            isolates.append(line.rstrip())
    return isolates

if len(sys.argv) != 5:
    sys.stdout.write('''
draw_timetable.py
USAGE: python draw_timetable.py <output.svg> <start date> <end date> <list of isolates>
Where

<output.svg> is the svg file created by this software

<start date> is the start of the date range to draw in format YYYY-MM-DD

<end date> is the end of the date range to draw in format YYYY-MM-DD

<list of isolates> is the list of isolates you want included in the SVG
e.g.
ER00001
CD00100
..
ER00200

''')
else:
    out_file = sys.argv[1]
    isolate_list = get_isolate_list(sys.argv[4])
    start_time = get_time(sys.argv[2])
    end_time = get_time(sys.argv[3])
    patients = get_dates(isolate_list)
    draw_timeline(patients, out_file, start_time, end_time, isolate_list)