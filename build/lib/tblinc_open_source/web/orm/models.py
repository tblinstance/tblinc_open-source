"""Declarative SQLite ORM with typed fields, QuerySet filtering, validation, and auto-migration."""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generic, Iterator, TypeVar

TModel = TypeVar("TModel", bound="Model")


class ValidationError(ValueError):
    """Raised when model field validation fails."""

    def __init__(self, errors: dict[str, str] | str) -> None:
        if isinstance(errors, str):
            self.errors = {"__all__": errors}
        else:
            self.errors = dict(errors)
        super().__init__(str(self.errors))


class DoesNotExist(LookupError):
    """Raised when QuerySet.get() matches zero rows."""


class MultipleObjectsReturned(LookupError):
    """Raised when QuerySet.get() matches more than one row."""


class Database:
    """Thread-safe SQLite database connection manager with schema registration."""

    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self._db_path = str(db_path)
        self._local = threading.local()
        self._lock = threading.RLock()
        self._memory_conn: sqlite3.Connection | None = None
        self._registered_models: list[type[Model]] = []

    @property
    def path(self) -> str:
        return self._db_path

    def configure(self, db_path: str | Path) -> None:
        with self._lock:
            self.close()
            self._db_path = str(db_path)

    def connection(self) -> sqlite3.Connection:
        if self._db_path == ":memory:":
            if self._memory_conn is None:
                conn = sqlite3.connect(":memory:", check_same_thread=False)
                conn.row_factory = sqlite3.Row
                conn.execute("PRAGMA foreign_keys = ON")
                self._memory_conn = conn
            return self._memory_conn

        conn = getattr(self._local, "conn", None)
        conn_path = getattr(self._local, "path", None)
        if conn is None or conn_path != self._db_path:
            Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(self._db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            self._local.conn = conn
            self._local.path = self._db_path
        return conn

    def execute(self, sql: str, params: tuple[Any, ...] | list[Any] = ()) -> sqlite3.Cursor:
        with self._lock:
            conn = self.connection()
            cur = conn.execute(sql, tuple(params))
            conn.commit()
            return cur

    def fetchall(self, sql: str, params: tuple[Any, ...] | list[Any] = ()) -> list[sqlite3.Row]:
        with self._lock:
            cur = self.connection().execute(sql, tuple(params))
            return cur.fetchall()

    def fetchone(self, sql: str, params: tuple[Any, ...] | list[Any] = ()) -> sqlite3.Row | None:
        with self._lock:
            cur = self.connection().execute(sql, tuple(params))
            return cur.fetchone()

    def register_model(self, model_cls: type[Model]) -> None:
        if model_cls not in self._registered_models:
            self._registered_models.append(model_cls)

    def migrate(self, models: list[type[Model]] | None = None) -> list[str]:
        """Create tables for all registered (or specified) ORM models."""
        targets = models if models is not None else list(self._registered_models)
        migrated: list[str] = []
        for cls in targets:
            cls.create_table(self)
            migrated.append(cls._meta["table"])
        return migrated

    def close(self) -> None:
        with self._lock:
            if self._memory_conn is not None:
                self._memory_conn.close()
                self._memory_conn = None
            conn = getattr(self._local, "conn", None)
            if conn is not None:
                conn.close()
                self._local.conn = None


# Default global database instance (reconfigurable per application)
default_db = Database(":memory:")


_LABEL_ACRONYMS = {"id": "ID", "ai": "AI", "uri": "URI", "url": "URL", "json": "JSON", "api": "API", "ms": "ms"}


class Field:
    """Base ORM column field descriptor."""

    sql_type: str = "TEXT"
    input_type: str = "text"

    def __init__(
        self,
        *,
        primary_key: bool = False,
        nullable: bool = False,
        blank: bool = False,
        unique: bool = False,
        default: Any = None,
        verbose_name: str | None = None,
        placeholder: str = "",
        help_text: str = "",
        choices: list[tuple[Any, str]] | None = None,
        suggestions: list[str] | None = None,
        editable: bool = True,
    ) -> None:
        self.name: str = ""
        self.primary_key = primary_key
        self.nullable = nullable
        self.blank = blank
        self.unique = unique
        self.default = default
        self.verbose_name = verbose_name
        self.placeholder = placeholder
        self.help_text = help_text
        self.choices = choices
        self.suggestions = list(suggestions) if suggestions else None
        self.editable = editable

    @property
    def label(self) -> str:
        if self.verbose_name:
            return self.verbose_name
        return " ".join(_LABEL_ACRONYMS.get(w.lower(), w.title()) for w in self.name.split("_") if w)

    def get_default(self) -> Any:
        return self.default() if callable(self.default) else self.default

    def column_ddl(self) -> str:
        parts = [f'"{self.name}"', self.sql_type]
        if self.primary_key:
            parts.append("PRIMARY KEY AUTOINCREMENT")
        else:
            if not self.nullable:
                parts.append("NOT NULL")
            if self.unique:
                parts.append("UNIQUE")
        return " ".join(parts)

    def to_python(self, value: Any) -> Any:
        return value

    def to_db(self, value: Any) -> Any:
        return value

    def validate(self, value: Any) -> Any:
        if value is None or value == "":
            if self.primary_key or self.nullable or self.blank:
                return None if self.nullable and value == "" else value
            raise ValueError(f"{self.label} is required.")
        coerced = self.to_python(value)
        if self.choices:
            valid = {c[0] for c in self.choices}
            if coerced not in valid and self.name == "model_key":
                try:
                    from ...ai_models import registry

                    resolved = registry.resolve_key(str(coerced))
                    if resolved in valid:
                        coerced = resolved
                except Exception:
                    pass
            if coerced not in valid:
                raise ValueError(f"{self.label} must be one of {sorted(map(str, valid))}.")
        return coerced


class AutoField(Field):
    sql_type = "INTEGER"
    input_type = "number"

    def __init__(self) -> None:
        super().__init__(primary_key=True, nullable=True, editable=False)

    def to_python(self, value: Any) -> int | None:
        return None if value is None else int(value)


class CharField(Field):
    sql_type = "TEXT"
    input_type = "text"

    def __init__(self, max_length: int = 255, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.max_length = max_length

    def to_python(self, value: Any) -> str:
        return str(value)

    def validate(self, value: Any) -> Any:
        val = super().validate(value)
        if val is not None and len(str(val)) > self.max_length:
            raise ValueError(f"{self.label} must be at most {self.max_length} characters.")
        return val


class EmailField(CharField):
    input_type = "email"

    def validate(self, value: Any) -> Any:
        val = super().validate(value)
        if val and ("@" not in val or "." not in val.split("@")[-1]):
            raise ValueError(f"{self.label} must be a valid email address.")
        return val


class PasswordField(CharField):
    input_type = "password"


class TextField(Field):
    sql_type = "TEXT"
    input_type = "textarea"

    def to_python(self, value: Any) -> str:
        return str(value)


class IntegerField(Field):
    sql_type = "INTEGER"
    input_type = "number"

    def to_python(self, value: Any) -> int:
        return int(value)


class FloatField(Field):
    sql_type = "REAL"
    input_type = "number"

    def to_python(self, value: Any) -> float:
        return float(value)


class BooleanField(Field):
    sql_type = "INTEGER"
    input_type = "checkbox"

    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("default", False)
        super().__init__(**kwargs)

    def to_python(self, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in {"1", "true", "yes", "on"}
        return bool(value)

    def to_db(self, value: Any) -> int:
        return 1 if self.to_python(value) else 0


class DateTimeField(Field):
    sql_type = "TEXT"
    input_type = "text"

    def __init__(self, auto_now_add: bool = False, auto_now: bool = False, **kwargs: Any) -> None:
        self.auto_now_add = auto_now_add
        self.auto_now = auto_now
        if auto_now_add or auto_now:
            kwargs.setdefault("default", lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))
            kwargs.setdefault("editable", False)
        super().__init__(**kwargs)

    def to_python(self, value: Any) -> str:
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M:%S")
        return str(value)


class JSONField(Field):
    sql_type = "TEXT"
    input_type = "textarea"

    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("default", dict)
        super().__init__(**kwargs)

    def to_python(self, value: Any) -> Any:
        if isinstance(value, str):
            text = value.strip()
            return json.loads(text) if text else {}
        return value

    def to_db(self, value: Any) -> str:
        if isinstance(value, str):
            return value
        return json.dumps(value)


class ForeignKey(IntegerField):
    """Foreign key storing the referenced model's primary key."""

    def __init__(self, to: type[Model], **kwargs: Any) -> None:
        self.to_model = to
        super().__init__(**kwargs)

    def column_ddl(self) -> str:
        base = super().column_ddl()
        ref_table = self.to_model._meta["table"]
        return f'{base} REFERENCES "{ref_table}"("id") ON DELETE CASCADE'


class QuerySet(Generic[TModel]):
    """Chainable lazy SQL query builder for ORM models."""

    def __init__(
        self,
        model_cls: type[TModel],
        db: Database | None = None,
        where: list[tuple[str, list[Any]]] | None = None,
        order: list[str] | None = None,
        limit_val: int | None = None,
        offset_val: int | None = None,
    ) -> None:
        self.model_cls = model_cls
        self.db = db or model_cls._db or default_db
        self._where = list(where) if where else []
        self._order = list(order) if order else []
        self._limit = limit_val
        self._offset = offset_val

    def _clone(self, **updates: Any) -> QuerySet[TModel]:
        return QuerySet(
            self.model_cls,
            db=self.db,
            where=updates.get("where", list(self._where)),
            order=updates.get("order", list(self._order)),
            limit_val=updates.get("limit_val", self._limit),
            offset_val=updates.get("offset_val", self._offset),
        )

    def _parse_lookup(self, key: str, value: Any, negate: bool = False) -> tuple[str, list[Any]]:
        parts = key.split("__", 1)
        col = parts[0]
        op = parts[1] if len(parts) == 2 else "exact"
        if col not in self.model_cls._fields:
            raise ValueError(f"Unknown field '{col}' on {self.model_cls.__name__}")
        field = self.model_cls._fields[col]

        if op == "exact":
            if value is None:
                clause = f'"{col}" IS NOT NULL' if negate else f'"{col}" IS NULL'
                return clause, []
            sql_op = "!=" if negate else "="
            return f'"{col}" {sql_op} ?', [field.to_db(value)]
        if op == "contains":
            clause = f'"{col}" NOT LIKE ?' if negate else f'"{col}" LIKE ?'
            return clause, [f"%{value}%"]
        if op == "icontains":
            clause = f'LOWER("{col}") NOT LIKE LOWER(?)' if negate else f'LOWER("{col}") LIKE LOWER(?)'
            return clause, [f"%{value}%"]
        if op in {"gt", "gte", "lt", "lte"}:
            map_op = {"gt": ">", "gte": ">=", "lt": "<", "lte": "<="}[op]
            clause = f'NOT ("{col}" {map_op} ?)' if negate else f'"{col}" {map_op} ?'
            return clause, [field.to_db(value)]
        if op == "in":
            vals = [field.to_db(v) for v in value]
            if not vals:
                return ("1=1" if negate else "1=0"), []
            placeholders = ", ".join("?" for _ in vals)
            kw = "NOT IN" if negate else "IN"
            return f'"{col}" {kw} ({placeholders})', vals
        raise ValueError(f"Unsupported lookup '__{op}'")

    def filter(self, **kwargs: Any) -> QuerySet[TModel]:
        new_where = list(self._where)
        for k, v in kwargs.items():
            new_where.append(self._parse_lookup(k, v, negate=False))
        return self._clone(where=new_where)

    def exclude(self, **kwargs: Any) -> QuerySet[TModel]:
        new_where = list(self._where)
        for k, v in kwargs.items():
            new_where.append(self._parse_lookup(k, v, negate=True))
        return self._clone(where=new_where)

    def search(self, query: str, fields: list[str]) -> QuerySet[TModel]:
        q = query.strip()
        if not q or not fields:
            return self
        clauses = []
        params: list[Any] = []
        for col in fields:
            if col in self.model_cls._fields:
                clauses.append(f'LOWER(CAST("{col}" AS TEXT)) LIKE LOWER(?)')
                params.append(f"%{q}%")
        if not clauses:
            return self
        new_where = [*self._where, ("(" + " OR ".join(clauses) + ")", params)]
        return self._clone(where=new_where)

    def order_by(self, *fields: str) -> QuerySet[TModel]:
        order_clauses: list[str] = []
        for item in fields:
            desc = item.startswith("-")
            col = item[1:] if desc else item
            if col not in self.model_cls._fields:
                raise ValueError(f"Unknown order_by field '{col}' on {self.model_cls.__name__}")
            order_clauses.append(f'"{col}" {"DESC" if desc else "ASC"}')
        return self._clone(order=order_clauses)

    def limit(self, n: int) -> QuerySet[TModel]:
        return self._clone(limit_val=int(n))

    def offset(self, n: int) -> QuerySet[TModel]:
        return self._clone(offset_val=int(n))

    def _build_where(self) -> tuple[str, list[Any]]:
        if not self._where:
            return "", []
        clauses = [c for c, _ in self._where]
        params = [p for _, ps in self._where for p in ps]
        return " WHERE " + " AND ".join(clauses), params

    def all(self) -> list[TModel]:
        table = self.model_cls._meta["table"]
        where_sql, params = self._build_where()
        order_sql = (" ORDER BY " + ", ".join(self._order)) if self._order else ""
        limit_sql = f" LIMIT {self._limit}" if self._limit is not None else ""
        offset_sql = f" OFFSET {self._offset}" if self._offset is not None else ""
        sql = f'SELECT * FROM "{table}"{where_sql}{order_sql}{limit_sql}{offset_sql}'
        rows = self.db.fetchall(sql, params)
        return [self.model_cls._from_row(row, db=self.db) for row in rows]

    def first(self) -> TModel | None:
        items = self.limit(1).all()
        return items[0] if items else None

    def get(self, **kwargs: Any) -> TModel:
        qs = self.filter(**kwargs) if kwargs else self
        items = qs.limit(2).all()
        if not items:
            raise DoesNotExist(f"{self.model_cls.__name__} matching query does not exist.")
        if len(items) > 1:
            raise MultipleObjectsReturned(f"Multiple {self.model_cls.__name__} records returned.")
        return items[0]

    def count(self) -> int:
        table = self.model_cls._meta["table"]
        where_sql, params = self._build_where()
        row = self.db.fetchone(f'SELECT COUNT(*) AS cnt FROM "{table}"{where_sql}', params)
        return int(row["cnt"]) if row else 0

    def exists(self) -> bool:
        return self.count() > 0

    def delete(self) -> int:
        table = self.model_cls._meta["table"]
        where_sql, params = self._build_where()
        cur = self.db.execute(f'DELETE FROM "{table}"{where_sql}', params)
        return cur.rowcount

    def __iter__(self) -> Iterator[TModel]:
        return iter(self.all())

    def __len__(self) -> int:
        return self.count()


class Manager(Generic[TModel]):
    """Model.objects entry point."""

    def __init__(self, model_cls: type[TModel]) -> None:
        self.model_cls = model_cls

    def get_queryset(self, db: Database | None = None) -> QuerySet[TModel]:
        return QuerySet(self.model_cls, db=db)

    def all(self) -> list[TModel]:
        return self.get_queryset().all()

    def filter(self, **kwargs: Any) -> QuerySet[TModel]:
        return self.get_queryset().filter(**kwargs)

    def exclude(self, **kwargs: Any) -> QuerySet[TModel]:
        return self.get_queryset().exclude(**kwargs)

    def search(self, query: str, fields: list[str]) -> QuerySet[TModel]:
        return self.get_queryset().search(query, fields)

    def order_by(self, *fields: str) -> QuerySet[TModel]:
        return self.get_queryset().order_by(*fields)

    def get(self, **kwargs: Any) -> TModel:
        return self.get_queryset().get(**kwargs)

    def first(self) -> TModel | None:
        return self.get_queryset().first()

    def count(self) -> int:
        return self.get_queryset().count()

    def create(self, **kwargs: Any) -> TModel:
        obj = self.model_cls(**kwargs)
        obj.save()
        return obj


class ModelMeta(type):
    """Metaclass collecting declared ORM fields and registering concrete models."""

    def __new__(mcs, name: str, bases: tuple[type, ...], namespace: dict[str, Any]) -> type:
        fields: dict[str, Field] = {}
        for base in reversed(bases):
            if hasattr(base, "_fields"):
                fields.update(base._fields)

        own_fields: dict[str, Field] = {}
        for attr, val in list(namespace.items()):
            if isinstance(val, Field):
                val.name = attr
                own_fields[attr] = val
                del namespace[attr]

        fields.update(own_fields)
        is_abstract = name == "Model" or namespace.get("__abstract__", False)
        if not is_abstract and not any(f.primary_key for f in fields.values()):
            pk = AutoField()
            pk.name = "id"
            fields = {"id": pk, **fields}

        meta_cls = namespace.get("Meta")
        table_name = getattr(meta_cls, "table_name", f"{name.lower()}s")
        verbose_name = getattr(meta_cls, "verbose_name", name)
        verbose_plural = getattr(meta_cls, "verbose_name_plural", f"{verbose_name}s")

        namespace["_fields"] = fields
        namespace["_meta"] = {
            "table": table_name,
            "model_name": name.lower(),
            "verbose_name": verbose_name,
            "verbose_name_plural": verbose_plural,
        }
        cls = super().__new__(mcs, name, bases, namespace)
        if not is_abstract:
            cls.objects = Manager(cls)  # type: ignore[attr-defined]
            default_db.register_model(cls)  # type: ignore[arg-type]
        return cls


class Model(metaclass=ModelMeta):
    """Base ORM Model supporting declarative fields, validation, and SQLite persistence."""

    __abstract__ = True
    _fields: dict[str, Field]
    _meta: dict[str, Any]
    _db: Database | None = None
    objects: Manager[Any]

    def __init__(self, **kwargs: Any) -> None:
        self._instance_db: Database | None = kwargs.pop("_db", None)
        for fname, field in self._fields.items():
            if fname in kwargs:
                setattr(self, fname, field.to_python(kwargs[fname]) if kwargs[fname] is not None else None)
            else:
                setattr(self, fname, field.get_default())

    @property
    def pk(self) -> Any:
        return getattr(self, "id", None)

    @classmethod
    def get_db(cls) -> Database:
        return cls._db or default_db

    @classmethod
    def create_table(cls, db: Database | None = None) -> None:
        target_db = db or cls.get_db()
        cols = ", ".join(field.column_ddl() for field in cls._fields.values())
        table = cls._meta["table"]
        target_db.execute(f'CREATE TABLE IF NOT EXISTS "{table}" ({cols})')
        existing_rows = target_db.fetchall(f'PRAGMA table_info("{table}")')
        existing_cols = {str(r["name"]) for r in existing_rows}
        for fname, field in cls._fields.items():
            if field.primary_key or fname in existing_cols:
                continue
            default_sql = "0" if field.sql_type in {"INTEGER", "REAL"} else "''"
            target_db.execute(f'ALTER TABLE "{table}" ADD COLUMN "{fname}" {field.sql_type} DEFAULT {default_sql}')

    @classmethod
    def _from_row(cls: type[TModel], row: sqlite3.Row, db: Database | None = None) -> TModel:
        data = {col: row[col] for col in row.keys()}
        return cls(_db=db, **data)

    def validate(self) -> None:
        errors: dict[str, str] = {}
        for fname, field in self._fields.items():
            if field.primary_key:
                continue
            raw = getattr(self, fname, None)
            if isinstance(field, DateTimeField) and field.auto_now:
                raw = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                setattr(self, fname, raw)
            try:
                cleaned = field.validate(raw)
                setattr(self, fname, cleaned)
            except (ValueError, TypeError) as exc:
                errors[fname] = str(exc)
        if errors:
            raise ValidationError(errors)

    def save(self: TModel, db: Database | None = None) -> TModel:
        self.validate()
        target_db = db or self._instance_db or self.get_db()
        table = self._meta["table"]
        non_pk = [f for f in self._fields.values() if not f.primary_key]

        if self.pk is None:
            cols = ", ".join(f'"{f.name}"' for f in non_pk)
            placeholders = ", ".join("?" for _ in non_pk)
            values = [f.to_db(getattr(self, f.name)) for f in non_pk]
            try:
                cur = target_db.execute(f'INSERT INTO "{table}" ({cols}) VALUES ({placeholders})', values)
            except sqlite3.IntegrityError as exc:
                raise ValidationError(f"Database integrity error: {exc}") from exc
            self.id = cur.lastrowid
        else:
            assignments = ", ".join(f'"{f.name}" = ?' for f in non_pk)
            values = [f.to_db(getattr(self, f.name)) for f in non_pk] + [self.pk]
            try:
                target_db.execute(f'UPDATE "{table}" SET {assignments} WHERE "id" = ?', values)
            except sqlite3.IntegrityError as exc:
                raise ValidationError(f"Database integrity error: {exc}") from exc
        return self

    def delete(self, db: Database | None = None) -> None:
        if self.pk is None:
            return
        target_db = db or self._instance_db or self.get_db()
        table = self._meta["table"]
        target_db.execute(f'DELETE FROM "{table}" WHERE "id" = ?', (self.pk,))
        self.id = None

    def to_dict(self, exclude: set[str] | None = None) -> dict[str, Any]:
        skip = exclude or set()
        return {fname: getattr(self, fname, None) for fname in self._fields if fname not in skip}

    def __str__(self) -> str:
        for candidate in ("name", "title", "username", "email"):
            if candidate in self._fields and getattr(self, candidate, None):
                return str(getattr(self, candidate))
        return f"{self.__class__.__name__}(#{self.pk})"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.pk!r}>"
