#!/usr/bin/env python3

#from __future__ import print_function
from flask import Flask, request, redirect, Response, abort, send_from_directory
import os
import sys
import json
import libGnuplotIO

gplot = None

CONFIG = {}
with open( "config.json", 'r' ) as handle:
	CONFIG = json.load( handle )


def extract_blocks( key, content ):
	lines = content.splitlines()
	out = {}
	cnt = 0

	in_block = False

	for line in lines:
		if in_block:
			if line.strip().startswith("::end"):
				in_block = False
				cnt += 1
				
			else:
				out[cnt].append( line )
		else:
			if line.strip().startswith("::%s" % key):
				out[cnt] = []
				in_block = True
	
	return out
				


app = Flask(__name__,static_url_path="/notewiki/static")

def render_page( fn, title, project ):
	template = ""
	with open( "templates/page.html", 'rb' ) as handle:
		template = handle.read()
	
	template = template.decode("utf-8")
	
	content = ""
	with open( fn, 'rb' ) as handle:
		content = handle.read().strip()
	
	html = template.replace( "##TITLE##", title )
	html = html.replace( "##PROJECT##", project )
	html = html.replace( "##CONTENT##", content.decode("utf-8") )
	return html

def raw_page( fn, title, project ):
	
	content = ""
	with open( fn, 'rb' ) as handle:
		content = handle.read().strip()
	
	return content




@app.route("/")
def index():
	return redirect("/notewiki/main/index")
	
@app.route("/notewiki/<project>/<page>", methods = ["GET"])
def show_page( project, page ):
	
	if project not in CONFIG["projects"]:
		abort( 404, description = "Project not found." )
	
	fn = os.path.join( "pages", page + ".page" )
	fn = os.path.join( CONFIG["projects"][project], fn )
	print( "fn", fn)



	new_page_fn = os.path.join( "pages", "_new" + ".page" )
	if os.path.exists( fn ):
		if "raw" in request.args:
			return raw_page( fn, page, project )
		return render_page( fn, page, project )
	else:
		if "raw" in request.args:
			return raw_page( new_page_fn, page, project )
		return render_page( new_page_fn, page, project )


@app.route("/notewiki/<project>/<page>/plot/<int:plot_id>", methods = ["GET"])
def plot_graph( project, page, plot_id ):
	global gplot

	if gplot is None:
		print( "spawning gnuplot process")
		gplot = libGnuplotIO.Gnuplot()
		gplot.set_inmemory_output()


	if project not in CONFIG["projects"]:
		abort( 404, description = "Project not found." )
	
	fn = os.path.join( "pages", page + ".page" )
	fn = os.path.join( CONFIG["projects"][project], fn )

	content = raw_page( fn, page, project )
	content = str( content, "utf-8" )
	plots = extract_blocks("plot", content)
	#print( "plot_graph", plots)

	if plot_id in plots:
		plot = "\r\n".join( plots[plot_id] )
		if "plot" in plot:
			gplot.load( "lightstyle-png.txt" )
			gplot( plot )
			image = gplot.read_output()
			return Response( image, mimetype="image/png")
			
		

	return Response( b"", mimetype="image/png")



@app.route("/notewiki/<project>/<page>", methods= ["POST"])
def save_page( project, page ):
	
	if project not in CONFIG["projects"]:
		abort( 404, description = "Project not found." )
	
	fn = os.path.join( "pages", page + ".page" )
	fn = os.path.join( CONFIG["projects"][project], fn )
	
	
	content = request.form["content"].encode("utf-8")
	
	with open( fn, 'wb' ) as handle:
		handle.write( content )
	
	
	return render_page( fn, page, project )


@app.route("/notewiki/<project>/static/<path:path>", methods = ["GET"])
def server_per_project_static( project, path ):
	
	if project not in CONFIG["projects"]:
		abort( 404, description = "Project not found." )
	
	dirfn = os.path.join( CONFIG["projects"][project], "static" )

	return send_from_directory( dirfn, path )



if __name__ == "__main__":
    app.run(debug=True)
