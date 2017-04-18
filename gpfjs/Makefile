all:


wdae:
	rm -rf dist/
	ng build --aot -e prod --bh '/gpfjs' -d '/static/gpfjs'
	mkdir -p ../SeqPipeline/python/wdae/gpfjs/static/gpfjs
	cp -r dist/* ../SeqPipeline/python/wdae/gpfjs/static/gpfjs
	rm ../SeqPipeline/python/wdae/gpfjs/static/gpfjs/*.map
	cp dist/index.html ../SeqPipeline/python/wdae/wdae/templates/