all:


wdae:
	rm -rf dist/
	ng build --aot -e prod --bh '/gpfjs' -d '/static/gpfjs'
	mkdir -p ../gpf/wdae/gpfjs/static/gpfjs
	cp -r dist/* ../gpf/wdae/gpfjs/static/gpfjs
	rm ../gpf/wdae/gpfjs/static/gpfjs/*.map
	# cp dist/index.html ../SeqPipeline/python/wdae/wdae/templates/