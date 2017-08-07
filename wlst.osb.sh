#!/bin/bash
#-----------------------------------------------------
# Arquivo:      wlst.osb.sh
# Descricao:    helper para a interface wlst.osb
# Uso: ./wlst.osb.sh [script python] [arg1] [argN] [...]
#----------------------------------------------------
env=$1

echo $@

target=/opt/scripts/
python_path=${target}/deploy-osb
env_file=${python_path}/conf/environment.yml



# set up WL_DOMAIN_HOME, the root directory of your Domain WebLogic installation
if [ $env == 'prod' ]; then
  if [ $4 == 'customization_file' ]; then
    color=$2
    preserve=$3
    custom_file_url=$5
    custom='customization_file'
    list_url=$6
  else
    color=$2
    preserve=$3
    list_url=$4
  fi

  WL_DOMAIN_HOME=`grep -A4 -w ${color} ${env_file} | grep wlcustomization_file_domain_home | sed -r 's,.*: (/.*),\1,g'`

else
  if [ $3 == 'customization_file' ]; then
    color=""
    preserve=$2
    custom_file_url=$4
    custom='customization_file'
    list_url=$5
  else
    color=$2
    preserve=$3
    list_url=$4
  fi

  WL_DOMAIN_HOME=`grep -A4 -w ${env}: ${env_file} | grep wl_domain_home | sed -r 's,.*: (/.*),\1,g'`
fi

echo 'teste' ${WL_DOMAIN_HOME}
# set up common environment
. "${WL_DOMAIN_HOME}/bin/setDomainEnv.sh" 1> /dev/null

cd ${python_path}

LIB_DIR=${python_path}/lib

for  i in `ls -1 ${LIB_DIR}`
do
        CLASSPATH=${CLASSPATH}:${LIB_DIR}/$i
done

${JAVA_HOME}/bin/java -classpath $CLASSPATH \
    -Dweblogic.MaxMessageSize=40000000 \
    -Dsun.lang.ClassLoader.allowArraySyntax=true \
    weblogic.WLST ${python_path}/osbImportWithDownload.py ${env} ${color} ${preserve} ${custom} ${custom_file_url} ${list_url}
