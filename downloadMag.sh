#!/bin/bash

#http://revistas.inpi.gov.br/txt/RM2567.zip

for i in {2452..2577}
do
    eval "curl http://revistas.inpi.gov.br/txt/RM$i.zip --output to_process/RM$i.zip"
done

