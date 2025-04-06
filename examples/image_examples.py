from notion.builders import BlockBuilder

# 首先創建 BlockBuilder 實例
builder = BlockBuilder(imgur_client_id='your_imgur_client_id')

# 然後使用實例方法
blocks = [
    BlockBuilder.text_block("以下是一些圖片："),  # 靜態方法
    builder.image_block(  # 實例方法
        "https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png",
        caption="Google Logo"
    ),
    builder.image_block(  # 實例方法
        "path/to/local/image.jpg",
        caption="本地圖片"
    )
]

# 批量處理多個圖片
def create_image_blocks(image_paths: list) -> list:
    return [
        builder.image_block(
            image_path,
            caption=f"圖片 {i+1}"
        )
        for i, image_path in enumerate(image_paths)
    ] 