# Generate your first pipeline

In this tutorial, you will generate documentation for an order service that publishes an event and a billing service that receives it. You will finish with a Markdown page and four PlantUML source files.

You need Python 3.10 or later and a terminal. The commands below use a POSIX shell. No broker or PlantUML installation is needed for this tutorial.

## Install the current checkout

From the repository root, create a virtual environment and install the project:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
asyncapi-mate --help
```

The help output lists a required `SOURCE` argument and a required `--output` option.

## Inspect the example

Open [`docs/examples/orders.yaml`](../examples/orders.yaml) in your checkout. It defines an `orders.created` channel with a message named `OrderCreated`.

Its two operations refer to that channel. The `x-applications` section assigns the sending operation to `order-service` and the receiving operation to `billing-service`:

```yaml
x-applications:
  order-service:
    summary: Publishes newly created orders.
    operations:
      - $ref: '#/operations/publishOrder'
  billing-service:
    summary: Receives orders for billing.
    operations:
      - $ref: '#/operations/consumeOrder'
```

These are references within the same file. Use the complete example when running the command.

## Generate the files

Choose a new output directory:

```bash
asyncapi-mate docs/examples/orders.yaml --output build/orders
```

A successful run logs `SUCCESS` and creates:

```text
build/orders/
├── asyncapi.md
├── asyncapi.puml
└── docs/diagrams/src/c4/components/EDA/
    ├── order-service.puml
    ├── billing-service.puml
    └── OrderCreated.puml
```

Both applications use `OrderCreated`, so there is one payload diagram for that message.

## Read the results

Open `build/orders/asyncapi.md`. You should see the title “Order events,” the project and broker information, and sections for both applications. Each operation includes the `NewOrder` JSON example.

Open `build/orders/asyncapi.puml`. It contains a queue for `orders.created` and components for both services. The sender points down to the queue; the receiver uses an upward arrow.

Open `build/orders/docs/diagrams/src/c4/components/EDA/OrderCreated.puml`. The class includes `+orderId: string` and `#total: number`. The `+` marks a required property; `#` marks an optional property.

The Markdown image links will not display diagrams yet: this command has written diagram sources, not images.

## Continue

To add your own applications, use [Describe applications](../how-to/describe-applications.md). To display the generated diagrams in a site, follow [Integrate the output](../how-to/integrate-output.md). For the reasoning behind the two diagram views, read [How rendering works](../explanation/rendering.md).
