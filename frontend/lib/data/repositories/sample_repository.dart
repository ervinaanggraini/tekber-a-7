import '../data_sources/local_storage.dart';

class SampleRepository {
  final LocalStorage localStorage;

  SampleRepository(this.localStorage);

  Future<String> fetchGreeting() async {
    final cached = await localStorage.read('greeting');
    if (cached != null) return cached;
    // Simulate fetch
    final fetched = 'Hello from SampleRepository';
    await localStorage.save('greeting', fetched);
    return fetched;
  }
}
