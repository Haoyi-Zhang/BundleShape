"""Draw the manuscript schematics directly as font-embedded vector PDFs.

Run: python figures/draw_schematics.py --output figures
Requires Python 3.9+ and Matplotlib. No TeX engine or network is used.
The diagrams express the defined model; they are not measurement plots.
"""
import argparse
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, Circle, FancyArrowPatch

plt.rcParams.update({'font.family':'STIXGeneral', 'mathtext.fontset':'stix',
                     'font.size':9, 'pdf.fonttype':42, 'ps.fonttype':42,
                     'text.usetex':False, 'axes.unicode_minus':False})
CM = 1 / 2.54

class Drawing:
    def __init__(self, bounds):
        x0,y0,x1,y1 = bounds
        self.fig = plt.figure(figsize=((x1-x0)*CM,(y1-y0)*CM))
        self.ax = self.fig.add_axes([0,0,1,1], xlim=(x0,x1), ylim=(y0,y1))
        self.ax.set_aspect('equal'); self.ax.axis('off')
        self.nodes = {}
        self.labels = []

    def text(self,x,y,label,size=9,ha='center',va='center'):
        artist=self.ax.text(x,y,label,fontsize=size,ha=ha,va=va,
                            linespacing=1.15,clip_on=False,zorder=4)
        self.labels.append([artist,None])
        return artist

    def box(self,name,x,y,w,h,label,dashed=False,shape='rect',size=9):
        style = {'edgecolor':'black','facecolor':'white','linewidth':.55,
                 'linestyle':(0,(4,3)) if dashed else 'solid', 'zorder':2}
        if shape == 'diamond':
            obj = Polygon([(x-w/2,y),(x,y+h/2),(x+w/2,y),(x,y-h/2)],**style)
        elif shape == 'circle': obj = Circle((x,y),w/2,**style)
        else: obj = Rectangle((x-w/2,y-h/2),w,h,**style)
        self.ax.add_patch(obj); self.text(x,y,label,size)
        self.labels[-1][1]=(x-w/2,y-h/2,x+w/2,y+h/2)
        self.nodes[name] = (x,y,w,h,shape)

    def point(self,name,side):
        x,y,w,h,_ = self.nodes[name]
        return {'n':(x,y+h/2),'s':(x,y-h/2),'e':(x+w/2,y),
                'w':(x-w/2,y),'nw':(x-w/2,y+h/2),
                'ne':(x+w/2,y+h/2),'c':(x,y)}[side]

    def line(self,points,dashed=False):
        xs,ys=zip(*points)
        self.ax.plot(xs,ys,color='black',linewidth=.55,
                     linestyle=(0,(4,3)) if dashed else 'solid',zorder=1)

    def arrow(self,p,q,dashed=False,via=()):
        points=[p,*via,q]
        if via:self.line(points[:-1],dashed)
        self.ax.add_patch(FancyArrowPatch(points[-2],points[-1],
                         arrowstyle='-|>',mutation_scale=7.5,linewidth=.55,
                         color='black',shrinkA=0,shrinkB=0,
                         linestyle=(0,(4,3)) if dashed else 'solid',zorder=1))

    def edge(self,a,b,sa='s',sb='n',**kwargs):
        self.arrow(self.point(a,sa),self.point(b,sb),**kwargs)

    def frame(self,x,y,w,h):
        self.ax.add_patch(Rectangle((x,y),w,h,fill=False,edgecolor='black',
                                   linewidth=.55,linestyle=(0,(4,3)),zorder=0))

    def save(self,out,name):
        # Fixed physical canvas: do not enlarge or rasterize the scientific figure.
        self.fig.canvas.draw()
        renderer=self.fig.canvas.get_renderer()
        x0,x1=self.ax.get_xlim();y0,y1=self.ax.get_ylim()
        for artist,node in self.labels:
            b=artist.get_window_extent(renderer).transformed(self.ax.transData.inverted())
            if b.x0<x0-.02 or b.x1>x1+.02 or b.y0<y0-.02 or b.y1>y1+.02:
                raise ValueError(name+': clipped label '+repr(artist.get_text()))
            if node and (b.x0<node[0]-.02 or b.x1>node[2]+.02 or b.y0<node[1]-.02 or b.y1>node[3]+.02):
                raise ValueError(name+': label exceeds node '+repr(artist.get_text()))
        self.fig.savefig(out/(name+'.pdf'),format='pdf',
                         metadata={'Creator':'Python Matplotlib','Producer':None,
                                   'CreationDate':None,'ModDate':None})
        plt.close(self.fig)

def draw(out):
    d=Drawing((-1.65,-1.85,7.15,3.15))
    for i,(y,left,right) in enumerate([
        (2.4,'Root HTML\nIDs: title, card','Relocated root HTML\nIDs: $i_0,i_1$'),
        (1.2,'Detail HTML\nID: details','Relocated detail\nHTML, ID: $i_2$'),
        (0,'Stylesheet\nclasses: heading, $\\ldots$','Relocated stylesheet\nclasses: $c_2$, $\\ldots$'),
        (-1.2,'Image','Relocated image')]):
        d.box('l'+str(i),0,y,2.85,.85,left,size=8.5)
        d.box('r'+str(i),5.5,y,2.85,.85,right,size=8.5)
        d.edge('l'+str(i),'r'+str(i),'e','w')
    d.text(2.75,2.7,'global resource map',size=8.5)
    d.save(out,'resource-map')

    d=Drawing((-2.5,-8.6,10,.95))
    for name,x,y,label in [
        ('left',0,0,'left bundle\ncaller supplied'),
        ('right',0,-2.4,'right bundle\ncaller supplied'),
        ('admit',4,0,'strict admission\nand event extraction'),
        ('res',8,0,'rooted resource\nlabels $r_k$'),
        ('names',8,-2.4,'ID/class anchors\n$i_k,c_k$'),
        ('local',4,-2.4,'exact local\ncanonical records'),
        ('decision',4,-4.9,'$\\mathcal{N}(B)$ vs.\n$\\mathcal{N}(B\\prime)$'),
        ('cert',8,-4.9,'producer: total maps,\nfirst mismatch, or\nfirst error')]:
        d.box(name,x,y,3.15,1.35 if name=='cert' else 1.2,label,size=8.5)
    d.box('check',4,-7.8,4.9,1.2,'checker reparses endpoints,\nvalidates schema, and replays',size=8.5)
    d.edge('left','admit','e','w')
    d.arrow(d.point('right','e'),d.point('admit','s'),via=[(2.2,-2.4),(2.2,-1.3),(4,-1.3)])
    d.edge('admit','res','e','w');d.edge('res','names')
    d.edge('names','local','w','e');d.edge('local','decision');d.edge('decision','cert','e','w')
    d.arrow(d.point('cert','s'),d.point('check','n'),via=[(8,-6.6),(4,-6.6)])
    d.arrow(d.point('left','w'),(4-4.9/2,-7.6),dashed=True,via=[(-2.2,0),(-2.2,-7.6)])
    d.arrow(d.point('right','w'),(4-4.9/2,-8),dashed=True,via=[(-1.8,-2.4),(-1.8,-8)])
    d.save(out,'canonical-pipeline')

    d=Drawing((-1.523,-1.831,6.543,1.716))
    for name,x,y,label in [
        ('l1',0,1.08,'First page\ndiv/left: $a$;\nspan/right: $b$'),
        ('l2',0,-.12,'Second page\ndiv/left: $a$;\nspan/right: $b$'),
        ('r1',5,1.08,'First page\ndiv/left: $x$;\nspan/right: $y$'),
        ('r2',5,-.12,'Second page\ndiv/left: $y$;\nspan/right: $x$')]:
        d.box(name,x,y,2.25,1.1,label,size=8.5)
    d.edge('l1','r1','e','w');d.text(2.5,1.4,'local map $a\\mapsto x$',size=8.5)
    d.edge('l2','r2','e','w');d.text(2.5,-.5,'local map $a\\mapsto y$',size=8.5)
    d.box('global',2.5,-1.4,4.2,.75,'both local checks pass\nno single global map exists',dashed=True,size=8.5)
    d.save(out,'global-coupling')

if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,default=Path(__file__).resolve().parent)
    output=parser.parse_args().output
    output.mkdir(parents=True,exist_ok=True)
    draw(output)
