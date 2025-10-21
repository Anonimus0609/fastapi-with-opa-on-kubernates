FROM openpolicyagent/opa:1.9.0

CMD ["run", "--server", "--addr=0.0.0.0:8181", "/policy/admin.rego"]