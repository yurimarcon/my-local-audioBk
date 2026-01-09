Quantidade de segmentos: 5947

Rodar o comando:

```sh
ls -tr result > file_list.txt
```

Na sequência rodar o comando:

```sh
ffmpeg -f concat -safe 0 -i file_list.txt -c copy output.mp3
```
# my-local-audioBk
