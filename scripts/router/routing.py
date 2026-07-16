"""Provider-neutral routing policy."""

from .models import RoutingError


def choose_configured_profile_host(hosts, requested_provider, requested_model):
    configured_hosts = [
        host
        for host in hosts
        if host["provider"] == requested_provider
        and host_supports_model(host, requested_model)
    ]
    if configured_hosts:
        return best_host(configured_hosts)
    return None


def host_supports_model(host, requested_model):
    return any(model_name_matches(requested_model, candidate) for candidate in host.get("models", []))


def model_name_matches(requested_model, candidate_model):
    requested = str(requested_model or "").strip().lower()
    candidate = str(candidate_model or "").strip().lower()
    if not requested or not candidate:
        return False
    if requested == candidate:
        return True
    requested_base = requested.split(":", 1)[0]
    candidate_base = candidate.split(":", 1)[0]
    return requested_base == candidate or requested == candidate_base or (
        requested == requested_base and candidate.startswith(f"{requested}:")
    )


def resolve_routing_profile(task_package, config):
    if task_package.get("routing_profile"):
        profile_name = task_package["routing_profile"]
        metadata = {"routing_profile": profile_name}
    elif task_package.get("task_complexity"):
        profile_name = task_package["task_complexity"]
        metadata = {"task_complexity": profile_name}
    else:
        return dict(task_package), {}

    profiles = config.get("routing", {}).get("profiles", {})
    profile = profiles.get(profile_name)
    if not profile:
        raise RoutingError(f"routing profile is not configured: {profile_name}")

    provider = profile.get("provider")
    model = profile.get("model")
    if not provider or not model:
        raise RoutingError(f"routing profile must include provider and model: {profile_name}")

    routed_task = dict(task_package)
    routed_task["provider"] = provider
    routed_task["model"] = model
    return routed_task, metadata


def best_host(host_statuses):
    return sorted(
        host_statuses,
        key=lambda host: (
            -int(host.get("priority", 0)),
            float(host.get("elapsed_ms", 0)),
        ),
    )[0]
