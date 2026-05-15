class UnsupportedFileFormatError(ValueError):
    """文件格式不支持时抛出。"""


class DuplicateMatchKeyError(ValueError):
    """匹配字段存在重复值时抛出。"""

    def __init__(
        self,
        message: str,
        *,
        duplicate_target_keys: list[str] | None = None,
        duplicate_source_keys: list[str] | None = None,
    ) -> None:
        super().__init__(message)
        self.duplicate_target_keys = duplicate_target_keys or []
        self.duplicate_source_keys = duplicate_source_keys or []
