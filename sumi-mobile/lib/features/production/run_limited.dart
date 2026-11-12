/// Executa [task] para cada item com no máximo [concurrency] em paralelo,
/// como o `mergeMap(..., 3)` do web. Falhas individuais não interrompem o lote.
Future<void> runLimited<T>(List<T> items, int concurrency, Future<void> Function(T item) task) async {
  var next = 0;
  Future<void> worker() async {
    while (next < items.length) {
      final item = items[next++];
      try {
        await task(item);
      } catch (_) {}
    }
  }

  await Future.wait(List.generate(concurrency, (_) => worker()));
}
