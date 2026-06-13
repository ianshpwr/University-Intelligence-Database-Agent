from exporters.json_exporter import JSONExporter

exporter = JSONExporter()

exporter.export_universities()
exporter.export_tuition()

print("JSON export completed")