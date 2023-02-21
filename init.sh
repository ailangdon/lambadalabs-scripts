#!/bin/bash

# install docker image
echo "Pulling docker container" > ~/init.log
docker pull ailangdon/pytorch-devel:latest

# get source
echo "Getting source code" >> ~/init.log
git clone https://github.com/ailangdon/transformerDatabase

# preparing shakespeare data
echo "Preparing shakespeare data" >> ~/init.log
docker run --rm -u $(id -u):$(id -g) -v $PWD/transformerDatabase:/project -w /project/data/shakespeare ailangdon/pytorch-devel python prepare.py

# preparing shakespare_char data
echo "Preparing shakespeare_char data" >> ~/init.log
docker run --rm -u $(id -u):$(id -g) -v $PWD/transformerDatabase:/project -w /project/data/shakespeare_char ailangdon/pytorch-devel python prepare.py

# preparing openwebtext
echo "Preparing openwebtext data" >> ~/init.log
docker run --rm -u $(id -u):$(id -g) -v $PWD/transformerDatabase:/project -w /project/data/openwebtext ailangdon/pytorch-devel python prepare.py

# preparing wikipedia
echo "Preparing wikipedia data" >> ~/init.log
docker run --rm -u $(id -u):$(id -g) -v $PWD/transformerDatabase:/project -w /project/data/wikipedia ailangdon/pytorch-devel python prepare.py

# done
echo "DONE" >> ~/init.log
