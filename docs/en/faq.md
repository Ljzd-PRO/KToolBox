# FAQ

## How to solve the failure of uvloop installation?

!!! info "It's optional"
    uvloop can improve concurrent performance, but it's **optional**. 
    If you don't want to install uvloop, you can ignore this step.

On **Windows**, uvloop is **not supported**. If you failed installing uvloop on Linux or macOS, 
you can try to install it with system package manager like **apt**, **yum** or **brew**, 
pacakge managers provide prebuilt wheels for uvloop.

- Install with apt
    ```bash
    sudo apt install python3-uvloop
    ```

## `attachments` folder inside post directory is no need for me

You can set configuration option `job.post_structure.attachments` to `./`

Set the configuration by `prod.env` dotenv file or system environment variables:
```dotenv
KTOOLBOX_JOB__POST_STRUCTURE__ATTACHMENTS=./
```

`./` means attachments will be downloaded directly into the post directory.

!!! info "Notice"
    For more information, please visit [Configuration-Guide](configuration/guide.md) page.

## Commands and flags should use `-` or `_` as seperator?

Both is support, `-` is suggested.