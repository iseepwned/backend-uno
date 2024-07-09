# Page

```python
class Component:
    """
    La interfaz base Component define las operaciones que pueden ser alteradas por 
    decoradores."""

    def operation(self) -> str:
        pass
```

```python
class ConcreteComponent(Component):
    """
    Los Componentes Concretos proporcionan implementaciones predeterminadas de 
    las operaciones.
    Puede haber varias variaciones de estas clases.
    """

    def operation(self) -> str:
        return "ConcreteComponent"
```

```python
class Decorator(Component):
    """
    La clase Decorador base sigue la misma interfaz que los otros componentes.
    El propósito principal de esta clase es definir la interfaz de envoltura para
    todos los decoradores concretos. La implementación predeterminada del código de
    envoltura puede incluir un campo para almacenar un componente envuelto y los 
    medios para inicializarlo.
    """

    _component: Component = None

    def __init__(self, component: Component) -> None:
        self._component = component

    @property
    def component(self) -> Component:
        # El Decorador delega todo el trabajo al componente envuelto.
        return self._component

    def operation(self) -> str:
        return self._component.operation()

```
