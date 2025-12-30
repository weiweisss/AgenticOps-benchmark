from typing import Any
from dataclasses import dataclass
from register import TEMPLATE_REGISTRY, EXPERIMENTS_DIR
from jinja2 import Environment, FileSystemLoader
import subprocess
import yaml

@dataclass
class FaultRequest:
    templateID: str           # template identifier from the registry
    metadata: dict[str, str]  # name, namespace, etc.
    spec: dict[str, Any]      # concrete parameters (selector, duration, etc.)

def router(templateID: str, metadata: dict[str, str], *, spec: dict[str, Any]) -> FaultRequest:
    """
    Constructs a normalized FaultRequest from user-specified inputs.

    Parameters:
        templateID: str:
            The identifier of the registered fault template
            to be used. This value is used to look up the template
            definition in the registry.

        metadata: dict[str, str]
            Metadata describing the fault instance. Expected keys include:
            - "name":        Optional. The name assigned to this fault instance.
                            A default name will be generated if omitted.
            - "namespace":   Optional. The namespace in which the fault should be applied.
                            Defaults to the framework’s configured namespace.

        spec: dict[str, Any]
            The specification of the fault, including both the target scope
            (e.g., selectors, namespaces) and all fault-specific parameters
            required by the chosen template.

    Returns:
        FaultRequest:
            A normalized, backend-agnostic request object that encapsulates all
            semantic information needed for downstream template resolution and
            backend execution.
    """
    if metadata.get("name") is None:
        metadata["name"] = f"{templateID.replace('/', '-')}-instance"
    if metadata.get("namespace") is None:
        metadata["namespace"] = "chaos-testing"
    return FaultRequest(
        templateID=templateID,
        metadata=metadata,
        spec=spec,
    )

def inject(request: FaultRequest) -> None:
    """
    Executes a fault-injection request by resolving the corresponding template
    and dispatching it to the appropriate backend.

    Parameters:
        request: FaultRequest
            A fully normalized fault request, containing:
            - templateID:    The identifier used to retrieve the registered
                              fault template from the TEMPLATE_REGISTRY.
            - metadata:      A dictionary describing contextual attributes of
                              the fault instance (e.g., name, namespace).
            - spec:          A dictionary defining the fault’s operational
                              parameters and target scope, already validated
                              against the template schema.

    Behavior:
        Based on the backend declared in the resolved template, this function:
        - For the "chaos-mesh" backend:
            * Loads the corresponding experiment template from the filesystem.
            * Applies Jinja2-based rendering using the request’s metadata and spec.
            * Converts intermediate structures into YAML through a custom
              `to_yaml` filter to ensure stable, readable formatting.
            * Submits the rendered manifest to Kubernetes via `kubectl apply -f -`.

        - For the "chaosd" backend:
            Reserved for future extensions; no operation is performed.

        - For the "custom" backend:
            Reserved for user-defined execution logic.
    """
    template = TEMPLATE_REGISTRY[request.templateID]

    if template.backend == "chaos-mesh":
        env = Environment(
            loader=FileSystemLoader(str(EXPERIMENTS_DIR)),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        def to_yaml(value):
            return yaml.dump(value, default_flow_style=False, sort_keys=False).rstrip()
        env.filters["to_yaml"] = to_yaml
        raw_yaml = env.get_template(template.template_path)
        rendered_yaml = raw_yaml.render(
            metadata=request.metadata,
            spec=request.spec,
        )
        subprocess.run(
            ["kubectl", "apply", "-f", "-"],
            input=rendered_yaml.encode("utf-8"),
            check=True,
        )

    elif template.backend == "chaosd":
        pass

    elif template.backend == "custom":
        pass

def main():
    req = router(
        templateID="cpu_throttling",
        metadata={
            "name": "test-cpu-throttling",
            "namespace": "default",
        },
        spec={
            "selector": {
                "pods": {
                    "liuhe": 
                    ["liuhe-demo-job-vsr96-worker-0"]
                }
            }
        }
    )
    inject(req)

if __name__ == "__main__":
    main()