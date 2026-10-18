// apple-fm judge shim.
// stdin:  {"prompt": "...", "schema": {<JSON Schema>}, "instructions": "..."?}
// stdout: one JSON value conforming to schema.
// exit:   0 ok, 2 model unavailable (reason on stderr), 1 any other error.
// Build:  xcrun swiftc -O -parse-as-library -target arm64-apple-macosx26.0 main.swift -o apple-fm
// The session is created with tools: [], so the model has nothing to call.
import Foundation
import FoundationModels

func fail(_ msg: String, _ code: Int32) -> Never {
    FileHandle.standardError.write((msg + "\n").data(using: .utf8)!)
    exit(code)
}

// GenerationSchema is Codable and decodes JSON Schema, but its decoder demands keys
// plain JSON Schema usually omits on every object schema: "title", "x-order",
// "additionalProperties" and "required". Fill the gaps: title is the JSON path
// (unique, so no duplicateType), x-order is required keys first then the rest sorted
// (JSONSerialization does not keep key order), additionalProperties false, required [].
func normalize(_ v: Any, _ path: String = "Result") -> Any {
    if let a = v as? [Any] { return a.enumerated().map { normalize($1, "\(path)_\($0)") } }
    guard var d = v as? [String: Any] else { return v }
    for (k, x) in d { d[k] = normalize(x, "\(path)_\(k)") }
    guard let props = d["properties"] as? [String: Any] else { return d }
    let req = (d["required"] as? [String] ?? []).filter { props[$0] != nil }
    if d["title"] == nil { d["title"] = path }
    if d["x-order"] == nil { d["x-order"] = req + props.keys.filter { !req.contains($0) }.sorted() }
    if d["additionalProperties"] == nil { d["additionalProperties"] = false }
    if d["required"] == nil { d["required"] = req }
    return d
}

@main
struct Shim {
    static func main() async {
        if case .unavailable(let reason) = SystemLanguageModel.default.availability {
            fail("unavailable: \(reason)", 2)
        }
        let prompt: String, instructions: String?, schema: GenerationSchema
        do {
            let obj = try JSONSerialization.jsonObject(with: FileHandle.standardInput.readDataToEndOfFile())
            guard let req = obj as? [String: Any], let p = req["prompt"] as? String, let s = req["schema"] else {
                fail("bad request: need {\"prompt\": string, \"schema\": object}", 1)
            }
            prompt = p
            instructions = req["instructions"] as? String
            schema = try JSONDecoder().decode(GenerationSchema.self,
                from: JSONSerialization.data(withJSONObject: normalize(s)))
        } catch { fail("bad request: \(error)", 1) }
        let session = LanguageModelSession(tools: [], instructions: instructions)
        do {
            let r = try await session.respond(
                to: prompt, schema: schema,
                options: GenerationOptions(samplingMode: .greedy))
            print(r.content.jsonString)
        } catch { fail("generation failed: \(error)", 1) }
    }
}
