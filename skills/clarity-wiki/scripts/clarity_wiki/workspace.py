"""Bounded reads inside an explicitly selected workspace."""

import os
from pathlib import Path
import stat


class InputError(ValueError):
    """Invalid or unsafe user input; safe to show without a traceback."""


class MissingFileError(InputError, FileNotFoundError):
    """A validated workspace path does not exist."""


class Workspace:
    def __init__(self, root: str | Path):
        self._root_fd = None
        try:
            if os.open not in os.supports_dir_fd or not hasattr(os, 'O_NOFOLLOW'):
                raise InputError('safe workspace reads require POSIX dir_fd and O_NOFOLLOW support')
            self.root = Path(root).expanduser().resolve(strict=True)
            if not self.root.is_dir():
                raise InputError('workspace root must be an existing directory')
            self._root_fd = self._anchor_root(self.root)
        except (OSError, RuntimeError, TypeError, ValueError) as error:
            raise InputError('workspace root must be an existing directory') from error

    @staticmethod
    def _anchor_root(root: Path) -> int:
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        descriptor = os.open(root.anchor, flags)
        try:
            for part in root.parts[1:]:
                child = os.open(part, flags, dir_fd=descriptor)
                os.close(descriptor)
                descriptor = child
            return descriptor
        except BaseException:
            os.close(descriptor)
            raise

    def close(self):
        if self._root_fd is not None:
            os.close(self._root_fd)
            self._root_fd = None

    def __del__(self):
        self.close()

    def _open_relative(self, parts: tuple[str, ...]) -> int:
        if self._root_fd is None:
            raise InputError('workspace is closed')
        descriptor = os.dup(self._root_fd)
        try:
            for index, part in enumerate(parts):
                flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, 'O_NONBLOCK', 0)
                if index < len(parts) - 1:
                    flags |= os.O_DIRECTORY
                child = os.open(part, flags, dir_fd=descriptor)
                os.close(descriptor)
                descriptor = child
            return descriptor
        except BaseException:
            os.close(descriptor)
            raise

    def _resolve(self, path: str | Path) -> Path:
        if (not isinstance(path, (str, Path)) or not str(path) or len(str(path)) > 4096
                or '\x00' in str(path) or any(0xD800 <= ord(char) <= 0xDFFF for char in str(path))):
            raise InputError('path must be a nonempty path of at most 4096 characters')
        try:
            candidate = Path(path)
            resolved = (self.root / candidate).resolve()
            resolved.relative_to(self.root)
        except (OSError, RuntimeError, ValueError) as error:
            raise InputError('path must stay inside the workspace root') from error
        return resolved

    def relative(self, path: str | Path) -> str:
        return self._resolve(path).relative_to(self.root).as_posix()

    def read_bytes(self, path: str | Path, max_bytes: int = 8_388_608) -> bytes:
        if type(max_bytes) is not int or not 1 <= max_bytes <= 8_388_608:
            raise InputError('read limit must be between 1 and 8388608 bytes')
        resolved = self._resolve(path)
        name = resolved.relative_to(self.root).as_posix()
        try:
            descriptor = self._open_relative(resolved.relative_to(self.root).parts)
            with os.fdopen(descriptor, 'rb') as stream:
                metadata = os.fstat(stream.fileno())
                if not stat.S_ISREG(metadata.st_mode):
                    raise InputError(f'expected a regular file: {name}')
                if metadata.st_size > max_bytes:
                    raise InputError(f'file exceeds {max_bytes} bytes: {name}')
                data = stream.read(max_bytes + 1)
                if len(data) > max_bytes:
                    raise InputError(f'file exceeds {max_bytes} bytes: {name}')
                return data
        except FileNotFoundError as error:
            raise MissingFileError(f'missing file: {name}') from error
        except OSError as error:
            raise InputError(f'cannot read regular file: {name}') from error

    def read_text(self, path: str | Path, max_bytes: int = 262_144) -> str:
        try:
            return self.read_bytes(path, max_bytes).decode('utf-8-sig')
        except UnicodeDecodeError as error:
            raise InputError(f'expected UTF-8 text: {self.relative(path)}') from error
