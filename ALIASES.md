# Aliases

## .bashrc

### Others
```bash
ls='ls --color=auto -F'
..='cd ..'
...='cd ../..'
....='cd ../../..'
ll='ls -lhF'
la='ls -lhA'
l='ls -CF'
rm='rm -i'
rf='rm -rfi'
cp='cp -i'
mv='mv -i'
mkdir='mkdir -p'
benchmark
webshare 9999
```

### Systemctl/Service
```bash
start='sudo systemctl start'
stop='sudo systemctl stop'
restart='sudo systemctl restart'
status='systemctl status'
enable='sudo systemctl enable'
disable='sudo systemctl disable'
reload='sudo systemctl reload'
# Or
start='sudo service'
stop='sudo service'
restart='sudo service'
status='service'
reload='sudo service'
```

### Network
```bash
ports='netstat -tulanp'
myip='curl -s ifconfig.me'
localip='hostname -I | cut -d" " -f1'
```

### System monitoring
```bash
topcpu='ps aux | sort -nrk 3,3 | head -n 10'
topmem='ps aux | sort -nrk 4,4 | head -n 10'
df='df -h'
du='du -h'
free='free -h'
```

### Security
```bash
chmod='chmod -v'
chown='chown -v'
chgrp='chgrp -v'
```

### Git
```bash
gs='git status'
ga='git add'
gc='git commit'
gp='git push'
gl='git pull'
gd='git diff'
```

### Docker
```bash
dps='docker ps'
dls='docker ps -a'
dim='docker images'
dlog='docker logs'
dstop='docker stop'
drm='docker rm'
drmi='docker rmi'
```

### Custom
```bash
aptuprd='sudo apt update && sudo apt upgrade -y && sudo apt dist-upgrade -y && sudo apt autoremove -y'
ducks='for item in .* *; do [ "$item" != "." ] && [ "$item" != ".." ] && [ -e "$item" ] && sudo du -hsx "$item"; done | sort -rh | head -10'
clean_journal_logs='sudo journalctl --vacuum-size=100M'
docker_stats='docker run --rm -ti --name=ctop  --volume /var/run/docker.sock:/var/run/docker.sock:ro quay.io/vektorlab/ctop:latest -s cpu'
```
