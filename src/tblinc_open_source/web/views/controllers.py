"""MTV view helpers and MVC class-based Controller primitives for tblinc.web."""

from __future__ import annotations

from typing import Any, Callable

from ..http import HtmlResponse, Http404, HttpError, JsonResponse, RedirectResponse, Request, Response
from ..orm import DoesNotExist, Model


def render(request: Request, template_name: str, context: dict[str, Any] | None = None, status: int = 200) -> HtmlResponse:
    """MTV-style template rendering helper bound to the active TblincApp."""
    if request.app is None:
        raise RuntimeError("Request is not bound to a TblincApp instance.")
    return request.app.render(request, template_name, context or {}, status=status)


class Controller:
    """MVC class-based controller dispatching HTTP verbs to methods (get, post, put, delete)."""

    http_method_names = ("get", "post", "put", "patch", "delete", "head")

    def __init__(self, **initkwargs: Any) -> None:
        for k, v in initkwargs.items():
            setattr(self, k, v)

    def dispatch(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        verb = request.method.lower()
        if verb == "head" and not hasattr(self, "head") and hasattr(self, "get"):
            verb = "get"
        handler = getattr(self, verb, None)
        if handler is None or verb not in self.http_method_names:
            raise HttpError(405, f"Method {request.method} not allowed on {self.__class__.__name__}.")
        return handler(request, *args, **kwargs)

    def render(self, request: Request, template_name: str, context: dict[str, Any] | None = None, status: int = 200) -> HtmlResponse:
        return render(request, template_name, context, status=status)

    def json(self, data: Any, status: int = 200) -> JsonResponse:
        return JsonResponse(data, status=status)

    def redirect(self, location: str, status: int = 302) -> RedirectResponse:
        return RedirectResponse(location, status=status)

    @classmethod
    def as_view(cls, **initkwargs: Any) -> Callable[..., Response]:
        def view(request: Request, *args: Any, **kwargs: Any) -> Response:
            instance = cls(**initkwargs)
            return instance.dispatch(request, *args, **kwargs)

        view.__name__ = cls.__name__
        view.__doc__ = cls.__doc__
        return view


class ModelController(Controller):
    """MVC Resource Controller providing JSON CRUD endpoints for any ORM Model."""

    model: type[Model]

    def get(self, request: Request, pk: int | None = None) -> Response:
        if pk is None:
            items = [obj.to_dict(exclude={"password"}) for obj in self.model.objects.order_by("-id").all()]
            return self.json({"model": self.model.__name__, "count": len(items), "results": items})
        try:
            obj = self.model.objects.get(id=pk)
        except DoesNotExist as exc:
            raise Http404(f"{self.model.__name__} #{pk} not found.") from exc
        return self.json(obj.to_dict(exclude={"password"}))

    def post(self, request: Request) -> Response:
        payload = request.json() if request.is_json else dict(request.POST)
        payload.pop("csrf_token", None)
        obj = self.model(**payload)
        obj.save()
        return self.json(obj.to_dict(exclude={"password"}), status=201)

    def delete(self, request: Request, pk: int) -> Response:
        try:
            obj = self.model.objects.get(id=pk)
        except DoesNotExist as exc:
            raise Http404(f"{self.model.__name__} #{pk} not found.") from exc
        obj.delete()
        return self.json({"deleted": True, "id": pk})
