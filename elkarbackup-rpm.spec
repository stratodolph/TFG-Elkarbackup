Name:           elkarbackup-rpm 
Version:        1.0
Release:        1%{?dist}
Summary:        Elkarbackup rpm server installer

Group:          Server
License:        Free
URL:            https://www.elkarbackup.org
Source0:        elkarbackup-rpm-1.0.tar.gz

Requires:       php-xml,wget,php-pdo,mysql,php,php-cli,httpd,php-posix,php-process,php-json,rsnapshot
Requires(pre):  shadow-utils

%define dir_inst /usr/local/elkarbackup
%define log /tmp/inst_elkarbackup.log
%define data_file elkarbackup-v1.2.7-0.tar.gz
%define data_url http://elkarbackuprpm.duckdns.org/des/%{data_file}
%define os_user elkarbackup
%define os_group elkarbackup
%define os_user_home %{dir_inst}/keys
%define http_conf %{dir_inst}/debian/etc/apache2/conf-available/elkarbackup.conf
%define sudo_dir /etc/sudoers.d
%define sudo_file %{sudo_dir}/elkarbackup
%define sudo_file_orig %{dir_inst}/debian/etc/sudoers.d/elkarbackup
%define def_config_file %{dir_inst}/app/config/parameters.yml
%define package_name elkarbackup-rpm-1.0-1.el6.x86_64

%description
Elkarbackup rpm server installer

%prep
%setup -q

%build
#%configure
#make %{?_smp_mflags}

%install

%pre
DIR_INST=%{dir_inst}
OS_USER_HOME=%{os_user_home}
LOG=%{log}

DIST=`cat /etc/redhat-release`
echo "Start installation:" >> $LOG
date >> $LOG
echo "Distro: "$DIST >> $LOG
DISTV=`cat /etc/redhat-release | grep -c "Fedora"`
PHPMYSQL=`rpm -qa | grep -c php-mysql`
PHPMYSQLND=`rpm -qa | grep -c php-mysqlnd`
if [ $DISTV -gt 0 ]; then
DISTV2=`cat /etc/redhat-release | cut -f3 -d ' '`
echo "Release: "$DISTV2 >> $LOG

  if [ $DISTV2 -gt 24 ]; then
     if [ $PHPMYSQLND -gt 0 ]; then
        echo "php-mysqlnd installed" >> $LOG
     else
        echo "php-mysqlnd not installed" >> $LOG
        echo "php-mysqlnd package is needed for this distro"
        exit 1;
     fi
  else
     if [ $PHPMYSQL -gt 0 ]; then
        echo "php-mysql installed" >> $LOG
     else
        echo "php-mysql not installed" >> $LOG
        echo "php-mysql package is needed for this distro"
        exit 1;
     fi
  fi
else
     if [ $PHPMYSQL -gt 0 ]; then
        echo "php-mysql installed" >> $LOG
     else
        echo "php-mysql not installed" >> $LOG
        echo "php-mysql package is needed for this distro"
        exit 1;
     fi
fi

PHPVER=`php -v | head -1 | cut -f2 -d ' '`
echo "PHP Version: "$PHPVER >> $LOG
PHPVER1=`echo $PHPVER | cut -f1 -d '.'`
PHPVER2=`echo $PHPVER | cut -f2 -d '.'`
if [ $PHPVER1 -gt 5 ]; then
   echo "Version greater than 5"
else
   if [ $PHPVER1 -eq 5 ] && [ $PHPVER2 -gt 5 ]; then
      echo "Version "$PHPVER" valid" >> $LOG
   else
      echo "PHP version: "$PHPVER" not valid" >> $LOG
      echo "Need upgrade PHP version to 5.6 or higher"
      exit 1
   fi
fi

service httpd status
ERR_APA=$?

if [ $ERR_APA -eq 3 ]; then
   echo "Apache service is not started"
   echo "Apache service not started" >> $LOG
   exit 1
fi

service mysqld status
ERR_DB=$?
service mariadb status
ERR_DB2=$?

if [ $ERR_DB -eq 3 ]; then
   echo "Mysql service is not started"
   echo "Mysql service not started" >> $LOG
   exit 1
else
   if [ $ERR_DB -gt 0 ] && [ $ERR_DB2 -gt 0 ]; then
      echo "MariaDB service is not started"
      echo "MariaDB service not started" >> $LOG
      exit 1
   fi
fi

if [ -d  "$DIR_INST" ]; then
   rm -rf $DIR_INST/*
   mkdir -p $OS_USER_HOME
   chmod 777 $OS_USER_HOME
else
   mkdir $DIR_INST
   mkdir -p $OS_USER_HOME
   chmod 777 $OS_USER_HOME
fi

getent group %{os_group} > /dev/null || groupadd -r %{os_group}
getent passwd %{os_user} > /dev/null || useradd -r -d %{os_user_home} -g %{os_group} %{os_user}
chown -R %{os_user}:%{os_group} $DIR_INST

#Comprobar si ya existe timezone
CONF_LINE=`grep -c "date.timezone=Europe/Madrid ;Elkarbackup config line" /etc/php.ini`
if [ $CONF_LINE -eq 0 ]; then
   echo "date.timezone=Europe/Madrid ;Elkarbackup config line" >> /etc/php.ini
fi
exit 0


%post
DIR_INST=%{dir_inst}
LOG=%{log}
DATA_FILE=%{data_file}
DATA_URL=%{data_url}
OS_USER=%{os_user}
OS_GROUP=%{os_group}
UNINS=0

cd $DIR_INST
wget $DATA_URL
tar xzf $DATA_FILE -C $DIR_INST

ERR=$?
if [ $ERR -gt 0 ]; then
    echo "Decompressing error" >> $LOG
    UNINS=1
fi


cp -r elkarbackup-elkarbackup-4a45d6d/* ./
rm -rf elkarbackup-elkarbackup-4a45d6d
chown -R $OS_USER:$OS_GROUP $DIR_INST

CONFIG_FILE=$DIR_INST/app/config/parameters.yml.dist
UPLOAD_DIR=`sed -n 's/^[ \t]*upload_dir:[ \t]*\([^ #\t]*\).*/\1/p' $CONFIG_FILE`
DB_HOST=`sed -n 's/^[ \t]*database_host:[ \t]*\([^ #\t]*\).*/\1/p' $CONFIG_FILE`
DB_NAME=`sed -n 's/^[ \t]*database_name:[ \t]*\([^ #\t]*\).*/\1/p' $CONFIG_FILE`
DB_USERNAME=`sed -n 's/^[ \t]*database_user:[ \t]*\([^ #\t]*\).*/\1/p' $CONFIG_FILE`
DB_USER_PASS=`sed -n 's/^[ \t]*database_password:[ \t]*\([^ #\t]*\).*/\1/p' $CONFIG_FILE`
BACKUP_DIR=`sed -n 's/^[ \t]*backup_dir:[ \t]*\([^ #\t]*\).*/\1/p' $CONFIG_FILE`
#OS_USER=%{os_user}
#OS_GROUP=%{os_group}
OS_USER_HOME=%{os_user_home}
HTTP_CONF=%{http_conf}
SUDO_DIR=%{sudo_dir}
SUDO_FILE=%{sudo_file}
SUDO_FILE_ORIG=%{sudo_file_orig}
DEF_CONFIG_FILE=%{def_config_file}


mkdir -p $UPLOAD_DIR
mkdir -p $BACKUP_DIR
chown -R $OS_USER:$OS_GROUP $DIR_INST
chown -R $OS_USER:$OS_GROUP $BACKUP_DIR

if [ "$DB_HOST" = localhost ]
then
   ST_USER="'$DB_USERNAME'@localhost"
else
   ST_USER="'$DB_USERNAME'"
fi

echo "CREATE DATABASE IF NOT EXISTS $DB_NAME DEFAULT CHARACTER SET utf8;" | mysql -u"root" -h"$DB_HOST"
echo "GRANT ALL ON $DB_NAME.* TO $ST_USER IDENTIFIED BY '$DB_USER_PASS';" | mysql -u"root" -h"$DB_HOST"


if [ ! -f $OS_USER_HOME/.ssh/id_rsa ]
then
  mkdir $OS_USER_HOME/.ssh
  chown -R $OS_USER:$OS_GROUP $DIR_INST
  ssh-keygen -t rsa -b 4096 -N '' -f $OS_USER_HOME/.ssh/id_rsa
  sed -i "s#public_key:.*#public_key: $OS_USER_HOME/.ssh/id_rsa.pub#" $DIR_INST/app/config/parameters.yml
fi

cd $DIR_INST
./bootstrap.sh

ERR=$?
if [ $ERR -gt 0 ]; then
    echo "bootstrap execution error" >> $LOG
    UNINS=1
fi


DEF_CONFIG_FILE=$DIR_INST/app/config/parameters.yml

rm -Rf $DIR_INST/app/cache/*

rm -f $DIR_INST/app/DoctrineMigrations/Version20130306101349.php
php $DIR_INST/app/console doctrine:migrations:migrate --no-interaction
ERR=$?
if [ $ERR -gt 0 ]; then
    echo "Error on doctrine migrations" >> $LOG
    UNINS=1
fi

rm -rf $DIR_INST/app/sessions/*

chmod 777 $UPLOAD_DIR

chown -R apache:apache $UPLOAD_DIR
chown -R $OS_USER:$OS_GROUP $OS_USER_HOME
chown apache:apache $DEF_CONFIG_FILE
chown -R $OS_USER:$OS_USER $BACKUP_DIR

if [ -f "/etc/httpd/conf/httpd.conf" ];then
    cp $HTTP_CONF /etc/httpd/conf.d/
    sed -i 's~/usr/share/elkarbackup/web~'$DIR_INST'/web~' /etc/httpd/conf.d/elkarbackup.conf
else
    echo "Apache config file does not exist" >> $LOG
    echo "Apache config file does not exist"
    UNINS=1
fi
service httpd restart

cp $DIR_INST/debian/etc/cron.d/elkarbackup /etc/cron.d/elkarbackup
sed -i "s/www-data/${OS_USER}/" /etc/cron.d/elkarbackup
sed -i "s@/usr/share/elkarbackup@${DIR_INST}@" /etc/cron.d/elkarbackup 


CONFIG_FILE=$DIR_INST/app/config/parameters.yml
UPLOAD_DIR=`sed -n 's/^[ \t]*upload_dir:[ \t]*\([^ #\t]*\).*/\1/p' $CONFIG_FILE`

if [ -d "$SUDO_DIR" ];then
    cp $SUDO_FILE_ORIG $SUDO_FILE
    sed -i -e "s#elkarbackup#$OS_USER#g" -e "s#\s*Cmnd_Alias\s*ELKARBACKUP_SCRIPTS.*#Cmnd_Alias ELKARBACKUP_SCRIPTS=$UPLOAD_DIR/*#" $SUDO_FILE
    chmod 0440 $SUDO_FILE
else
    echo "sudo directory does not exist"
    echo "SUDO directory does not exist" >> $LOG
    UNINS=1
fi

php $DIR_INST/app/console elkarbackup:create_admin
ERR=$?
if [ $ERR -gt 0 ]; then
    echo "Error on create_admin" >> $LOG
    UNINS=1
fi

php $DIR_INST/app/console cache:clear --env=prod
ERR=$?
if [ $ERR -gt 0 ]; then
    echo "Error on cache:clear" >> $LOG
    UNINS=1
fi

php $DIR_INST/app/console assetic:dump --env=prod
ERR=$?
if [ $ERR -gt 0 ]; then
    echo "Error on assetic:dump" >> $LOG
    UNINS=1
fi

rm -rf $DIR_INST/app/sessions/*

chcon -t httpd_sys_rw_content_t $DIR_INST/app/cache/ -R
chcon -t httpd_sys_rw_content_t $DIR_INST/app/sessions/ -R
chcon -t httpd_sys_rw_content_t $DIR_INST/app/logs/ -R

service httpd restart
#Si algun error rollback, rpm -e ?

if [ $UNINS -gt 0 ]; then
    echo "Installation with errors, uninstalling..."
    rpm -e %{package_name}
else
    echo "Installation complete"
fi

%clean
rm -rf $RPM_BUILD_ROOT


%files
#%defattr(-,root,root,-)
#%doc

%changelog
