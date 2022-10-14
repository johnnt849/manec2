# AWS Instance Manager
A simple AWS Instance manager I made to use instances in group. For example, running SSH commands or sending files or syncing code to many instances with a single command.
Basic usage is creating instance groups with a particular context.
Inspired by the `ec2man` module made for [Dorylus](https://github.com/uclasystem/dorylus).

## Usage
```bash
python -m manec2 [ec2|asg]
```

### ec2 usage
```bash
positional arguments:
  command
    contexts
    create
    terminate
    start
    stop
    reboot
    image
    info
    ssh
    rsync
    scp
```

After creating an instance group on EC2 with a particular name (the name field for ALL instances is `test` for example), you can run a command like
`python -m manec2 ssh test -c "ls"` to get the results of the `ls` command from all instances.