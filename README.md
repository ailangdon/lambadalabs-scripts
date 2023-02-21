# Lambdalabs scripts
These python scripts enable to start up, setup, and stop instances on Lambdalabs and are intended to be used as part of a training script, e.g. to starts an instance, run training, downloads the training results and shutsdown all instances afterwards.

## Prerequisites
Install Python dependencies:
```
pip install -r requirements.txt
```

Create API key in your Lambdalabs account and export it as environment variable:
```
export API_KEY_LAMBDA_LABs=a.....
```

Create an ssh key in your Lambdalabs account. Store the pem file in ```~/.ssh/``` folder. The script will use the first ssh key in your Lambdalabs account.

## Start instance
If no GPU type is specified, by default ```gpu_1x_a10``` is used. To start the instance:
```
python startupInstance.py [GPU_TYPE]
```

If an instance already exists, no new instance is started (preventing accidential cost). Once the instance started up the ```init.sh``` script is copied onto the instance and executed. The ```init.sh``` in this repo is only an example script to download a docker container and prepare some training data. It could also be used to start training.

## Stop instance
ALL instances in the account will be terminated immediately.
