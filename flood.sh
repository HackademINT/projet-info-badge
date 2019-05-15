#!/bin/bash

while true; do 
  test_date=$(date -d "$((RANDOM%1+2010))-$((RANDOM%12+1))-$((RANDOM%28+1)) $((RANDOM%23+1)):$((RANDOM%59+1)):$((RANDOM%59+1))" '+%Y-%m-%d %H:%M:%S')
  test_id=$(( ( RANDOM % 10 )  + 1 ))
  id_ldap_teacher=$(( ( RANDOM % 4 )  + 1 ))
  id_ldap_student=$(( ( RANDOM % 4 )  + 1 ))
  id_module=$(( ( RANDOM % 12 )  + 0 ))
  echo "INSERT INTO badge (id_ldap_teacher,id_ldap_student, timestamp,id_module)
  VALUES('$id_ldap_teacher','$id_ldap_student','$test_date','$id_module')" | sudo -u postgres psql postgres
  echo $test_date
done
