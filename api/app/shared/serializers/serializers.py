def serialize_application_component(application_component):
    """
    Serialize an ApplicationComponent for use in Kubernetes templates.
    Includes information from component, instance, application and environment.

    Note: application_name is prefixed with the Tron namespace prefix (default: tron-ns-)
    to create isolated namespaces that don't conflict with existing cluster resources.
    """
    # Make a copy of settings to avoid modifying the original
    import copy

    from app.shared.config import get_namespace_for_application

    settings = (
        copy.deepcopy(application_component.settings)
        if application_component.settings
        else {}
    )

    # Ensure command is always a list when not None
    # This is necessary because the schema can return string, list or None
    # but templates expect list or None
    if settings and "command" in settings:
        command = settings.get("command")
        if command is not None:
            # If already a list, keep as is
            if isinstance(command, list):
                pass  # Already a list
            # If string, convert to list (already processed by schema, but ensure)
            elif isinstance(command, str):
                import shlex

                command_str = command.strip()
                if command_str:
                    settings["command"] = shlex.split(command_str)
                else:
                    settings["command"] = None
            # If None, keep None
        else:
            settings["command"] = None

    # Ensure all settings fields are preserved
    # This is important for fields like schedule, cpu, memory, envs, etc.
    # deepcopy already does this, but we ensure explicitly
    if not settings:
        settings = {}

    # Ensure webapps always have exposure defined
    component_type = (
        application_component.type.value
        if hasattr(application_component.type, "value")
        else str(application_component.type)
    )
    if component_type == "webapp" and "exposure" not in settings:
        settings["exposure"] = {"type": "http", "port": 80, "visibility": "cluster"}
    elif component_type == "webapp" and settings.get("exposure") is None:
        settings["exposure"] = {"type": "http", "port": 80, "visibility": "cluster"}

    # Convert Enums to strings in settings (especially exposure.visibility)
    if (
        settings
        and "exposure" in settings
        and isinstance(settings.get("exposure"), dict)
    ):
        exposure = settings["exposure"]
        if "visibility" in exposure:
            # If visibility is an Enum, convert to string
            visibility_value = exposure["visibility"]
            if hasattr(visibility_value, "value"):
                exposure["visibility"] = visibility_value.value
            elif not isinstance(visibility_value, str):
                exposure["visibility"] = str(visibility_value)

    # Generate namespace name with Tron prefix
    app_name = application_component.instance.application.name
    namespace_name = get_namespace_for_application(app_name)

    return {
        "component_name": application_component.name,
        "component_uuid": str(application_component.uuid),
        "component_type": application_component.type.value
        if hasattr(application_component.type, "value")
        else str(application_component.type),
        "application_name": namespace_name,
        "application_uuid": str(application_component.instance.application.uuid),
        "environment": application_component.instance.environment.name,
        "environment_uuid": str(application_component.instance.environment.uuid),
        "image": application_component.instance.image,
        "version": application_component.instance.version,
        "url": application_component.url,
        "enabled": application_component.enabled,
        "settings": settings,
    }


# Kept for compatibility (deprecated)
def serialize_webapp_deploy(webapp_deploy):
    return serialize_application_component(webapp_deploy)


def serialize_settings(settings):
    serialized_settings = {}

    for item in settings:
        serialized_settings.update({item.key: item.value})

    return serialized_settings
