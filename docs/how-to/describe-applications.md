# Describe applications in your document

Use this guide to associate existing AsyncAPI operations with the services that perform them. Start with a document containing channels and operations; the [tutorial example](../examples/orders.yaml) provides a working structure.

## Select the message for each channel

Place the message used for documentation under `channel.messages.defaultMessage`. Include a message `name`, a payload schema, and an `examples` list. The current renderer selects that key explicitly, so a channel containing only differently named message entries will not work with these templates.

## Add the application mapping

Add one entry per application under `x-applications`. Give it a summary and a list of operation references:

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

Use `send` on the publishing operation and `receive` on the receiving operation. Both operations may refer to the same channel.

## Generate and inspect

```bash
asyncapi-mate asyncapi.yaml --output build/application-review
```

Check `asyncapi.md` for an application section per entry. Check each application's `.puml` file under `docs/diagrams/src/c4/components/EDA/` for the expected channel and arrow direction.

If examples are missing from the overview, check that at least one sending operation uses the channel: overview queue definitions and examples are collected from send operations. Application diagrams include channels for both actions.

See [Input reference](../reference/input.md) for all fields consumed by the renderer.
