class SymptomAnalysis {
  String bodyArea;
  String symptoms;
  String severity;
  String duration;

  SymptomAnalysis({
    this.bodyArea = '',
    this.symptoms = '',
    this.severity = '',
    this.duration = '',
  });

  @override
  String toString() {
    return '''
Body Area : $bodyArea
Symptoms : $symptoms
Severity : $severity
Duration : $duration
''';
  }
}