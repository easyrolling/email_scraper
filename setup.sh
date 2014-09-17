scp -i /Users/waleup/Dropbox/waleup/primary.pem /Users/waleup/Dropbox/robot/harvester.py ubuntu@${1}:/home/ubuntu/
ssh -i /Users/waleup/Dropbox/waleup/primary.pem ubuntu@${1} -t 'sudo python harvester.py'

