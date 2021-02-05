from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import Executable, ClauseElement


class CreateView(Executable, ClauseElement):
    def __init__(self, name, select):
        self.name = name
        self.select = select


@compiles(CreateView)
def visit_create_view(element, compiler, **kw):
    create = "CREATE VIEW {name} AS {sql}".format(
        name=element.name,
        sql=compiler.process(element.select, literal_binds=True)
    )
    print(create)
    return create
