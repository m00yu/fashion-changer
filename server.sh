IMAGE_NAME="m00yu/server:0.1"

# 이미지가 존재하는지 확인
if docker image inspect "$IMAGE_NAME" > /dev/null 2>&1; then
    echo "이미지 $IMAGE_NAME 존재합니다."
else
    echo "이미지 $IMAGE_NAME 존재하지 않습니다. 이미지를 pull합니다."
    docker pull "$IMAGE_NAME"
fi

docker run -d --name server -p 80:8000\
    "$IMAGE_NAME"