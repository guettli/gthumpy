# $Id: make-tgz.sh 24 2006-12-08 21:06:14Z guettli $
# $HeadURL: file:///home/guettli/svn/gthumpy/trunk/src/make-tgz.sh $
cd `dirname $0`
rm -f *~ *.pyc
number-html-headings.py README-source.html README.html
my-html-tidy.sh README-source.html
cd ..
DATE=`date --iso`
dest=gthumpy-$DATE
cp -r src $dest || exit
find $dest -name '.svn' -type d | xargs rm -rf
tar -czf download/$dest.tgz $dest
rm -rf $dest
echo "Created ../download/$dest.tgz"
