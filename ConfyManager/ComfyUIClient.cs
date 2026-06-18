using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;

namespace ConfyManager;

public class ComfyUIClient : IDisposable
{
    private readonly HttpClient _http;
    private readonly string _baseUrl;

    public ComfyUIClient(string baseUrl = "http://127.0.0.1:8188")
    {
        _baseUrl = baseUrl.TrimEnd('/');
        _http = new HttpClient
        {
            BaseAddress = new Uri(_baseUrl),
            Timeout = TimeSpan.FromMinutes(10)
        };
    }

    public async Task<bool> CheckConnectionAsync()
    {
        try
        {
            var response = await _http.GetAsync("/system_stats");
            return response.IsSuccessStatusCode;
        }
        catch
        {
            return false;
        }
    }

    public async Task<string> UploadImageAsync(string imagePath)
    {
        using var form = new MultipartFormDataContent();
        var imageBytes = await File.ReadAllBytesAsync(imagePath);
        var imageContent = new ByteArrayContent(imageBytes);
        imageContent.Headers.ContentType = new MediaTypeHeaderValue("image/png");
        form.Add(imageContent, "image", Path.GetFileName(imagePath));
        form.Add(new StringContent("true"), "overwrite");

        var response = await _http.PostAsync("/upload/image", form);
        response.EnsureSuccessStatusCode();

        var json = await response.Content.ReadAsStringAsync();
        var result = JsonNode.Parse(json);
        return result?["name"]?.GetValue<string>() ?? Path.GetFileName(imagePath);
    }

    public async Task<string> QueuePromptAsync(JsonNode workflow)
    {
        var payload = new JsonObject { ["prompt"] = workflow.DeepClone() };
        var content = new StringContent(
            payload.ToJsonString(),
            Encoding.UTF8,
            "application/json"
        );

        var response = await _http.PostAsync("/prompt", content);
        response.EnsureSuccessStatusCode();

        var json = await response.Content.ReadAsStringAsync();
        var result = JsonNode.Parse(json);
        return result?["prompt_id"]?.GetValue<string>()
            ?? throw new Exception("ComfyUI não retornou prompt_id");
    }

    public async Task<JsonNode?> WaitForCompletionAsync(string promptId, CancellationToken ct = default)
    {
        while (!ct.IsCancellationRequested)
        {
            await Task.Delay(1500, ct);

            var response = await _http.GetAsync($"/history/{promptId}", ct);
            if (!response.IsSuccessStatusCode) continue;

            var json = await response.Content.ReadAsStringAsync(ct);
            var history = JsonNode.Parse(json);
            var promptResult = history?[promptId];
            if (promptResult == null) continue;

            var statusStr = promptResult["status"]?["status_str"]?.GetValue<string>();
            if (statusStr == "success")
                return promptResult;

            var completed = promptResult["status"]?["completed"]?.GetValue<bool>() ?? false;
            if (completed && statusStr != "success")
                throw new Exception($"ComfyUI retornou status: {statusStr}");
        }

        throw new OperationCanceledException();
    }

    public async Task<byte[]> DownloadImageAsync(string filename, string subfolder = "", string type = "output")
    {
        var url = $"/view?filename={Uri.EscapeDataString(filename)}" +
                  $"&subfolder={Uri.EscapeDataString(subfolder)}" +
                  $"&type={Uri.EscapeDataString(type)}";

        var response = await _http.GetAsync(url);
        response.EnsureSuccessStatusCode();
        return await response.Content.ReadAsByteArrayAsync();
    }

    public void Dispose() => _http.Dispose();
}
