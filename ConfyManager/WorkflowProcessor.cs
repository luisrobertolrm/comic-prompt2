using System.Text.Json;
using System.Text.Json.Nodes;
using ConfyManager.Models;

namespace ConfyManager;

public static class WorkflowProcessor
{
    private static readonly string[] NegativeKeywords =
        ["lowres", "worst quality", "bad anatomy", "bad hands", "error", "ugly", "deformed"];

    public record WorkflowNodes(
        string? PositivePromptNode,
        string? LatentImageNode,
        string? LoadImageNode,
        string? SaveImageNode,
        string? KSamplerNode
    );

    public static async Task<int> ProcessAsync(
        string workflowPath,
        string datasetPath,
        string outputDir,
        string comfyUrl,
        Action<string> onStatus,
        Action<int, int> onProgress)
    {
        var workflowJson = await File.ReadAllTextAsync(workflowPath);
        var workflowTemplate = JsonNode.Parse(workflowJson)
            ?? throw new Exception("JSON do workflow inválido");

        var datasetJson = await File.ReadAllTextAsync(datasetPath);
        var dataset = JsonSerializer.Deserialize<MassaDataset>(datasetJson)
            ?? throw new Exception("JSON do dataset inválido");

        Directory.CreateDirectory(outputDir);

        using var client = new ComfyUIClient(comfyUrl);

        onStatus("Verificando conexão com ComfyUI...");
        if (!await client.CheckConnectionAsync())
            throw new Exception($"ComfyUI não está acessível em {comfyUrl}. Verifique se está rodando.");

        // Upload da imagem de referência
        onStatus("Enviando imagem de referência para ComfyUI...");
        var imagemRef = dataset.Config.ImagemReferencia;
        if (!File.Exists(imagemRef))
            throw new FileNotFoundException($"Imagem de referência não encontrada: {imagemRef}");

        var uploadedName = await client.UploadImageAsync(imagemRef);

        // Identificar nós do workflow
        var nodes = IdentifyNodes(workflowTemplate);
        if (nodes.PositivePromptNode == null)
            throw new Exception("Nó de prompt positivo (CLIPTextEncode) não encontrado no workflow");

        int processados = 0;

        for (int i = 0; i < dataset.Registros.Count; i++)
        {
            var reg = dataset.Registros[i];
            onProgress(i + 1, dataset.Registros.Count);
            onStatus($"Enviando prompt {reg.Id}/{dataset.Registros.Count}...");

            // Clonar workflow
            var workflow = JsonNode.Parse(workflowTemplate.ToJsonString())!;

            // Modificar nós
            ModifyWorkflow(workflow, nodes, reg, dataset.Config, uploadedName, i);

            // Enfileirar no ComfyUI
            var promptId = await client.QueuePromptAsync(workflow);

            // Aguardar conclusão
            onStatus($"Aguardando imagem {reg.Id}/{dataset.Registros.Count}...");
            var result = await client.WaitForCompletionAsync(promptId);

            // Baixar imagens e salvar .txt
            var saved = await SaveOutputsAsync(client, result, reg, outputDir, i);
            if (saved) processados++;
        }

        return processados;
    }

    private static WorkflowNodes IdentifyNodes(JsonNode workflow)
    {
        string? positiveNode = null;
        string? latentNode = null;
        string? loadImageNode = null;
        string? saveImageNode = null;
        string? kSamplerNode = null;

        foreach (var prop in workflow.AsObject())
        {
            var key = prop.Key;
            var node = prop.Value;
            var classType = node?["class_type"]?.GetValue<string>();

            switch (classType)
            {
                case "CLIPTextEncode":
                    var text = node?["inputs"]?["text"]?.GetValue<string>() ?? "";
                    var isNegative = NegativeKeywords.Any(k =>
                        text.Contains(k, StringComparison.OrdinalIgnoreCase));
                    if (!isNegative)
                        positiveNode ??= key;
                    break;

                case "EmptyLatentImage":
                    latentNode = key;
                    break;

                case "LoadImage":
                    loadImageNode = key;
                    break;

                case "SaveImage":
                    saveImageNode = key;
                    break;

                case "KSampler":
                    kSamplerNode = key;
                    break;
            }
        }

        return new WorkflowNodes(positiveNode, latentNode, loadImageNode, saveImageNode, kSamplerNode);
    }

    private static void ModifyWorkflow(
        JsonNode workflow,
        WorkflowNodes nodes,
        MassaRegistro registro,
        MassaConfig config,
        string uploadedImageName,
        int index)
    {
        // Atualizar prompt positivo
        if (nodes.PositivePromptNode != null)
        {
            workflow[nodes.PositivePromptNode]!["inputs"]!["text"] = registro.Prompt;
        }

        // Atualizar resolução
        if (nodes.LatentImageNode != null)
        {
            workflow[nodes.LatentImageNode]!["inputs"]!["width"] = config.Largura;
            workflow[nodes.LatentImageNode]!["inputs"]!["height"] = config.Altura;
        }

        // Atualizar imagem de referência
        if (nodes.LoadImageNode != null)
        {
            workflow[nodes.LoadImageNode]!["inputs"]!["image"] = uploadedImageName;
        }

        // Atualizar prefixo do nome do arquivo
        if (nodes.SaveImageNode != null)
        {
            workflow[nodes.SaveImageNode]!["inputs"]!["filename_prefix"] =
                $"massa_{index + 1:D4}";
        }

        // Randomizar seed
        if (nodes.KSamplerNode != null)
        {
            workflow[nodes.KSamplerNode]!["inputs"]!["seed"] = Random.Shared.NextInt64();
        }
    }

    private static async Task<bool> SaveOutputsAsync(
        ComfyUIClient client,
        JsonNode? result,
        MassaRegistro registro,
        string outputDir,
        int index)
    {
        if (result?["outputs"] is not JsonNode outputs)
            return false;

        bool saved = false;

        foreach (var nodeProp in outputs.AsObject())
        {
            var images = nodeProp.Value?["images"]?.AsArray();
            if (images == null) continue;

            foreach (var img in images)
            {
                var filename = img?["filename"]?.GetValue<string>();
                var subfolder = img?["subfolder"]?.GetValue<string>() ?? "";
                var type = img?["type"]?.GetValue<string>() ?? "output";

                if (string.IsNullOrEmpty(filename)) continue;

                // Baixar imagem
                var imageBytes = await client.DownloadImageAsync(filename, subfolder, type);

                // Salvar com nome padronizado
                var baseName = $"massa_{index + 1:D4}";
                var ext = Path.GetExtension(filename);
                if (string.IsNullOrEmpty(ext)) ext = ".png";

                var imagePath = Path.Combine(outputDir, $"{baseName}{ext}");
                await File.WriteAllBytesAsync(imagePath, imageBytes);

                // Salvar .txt com conteúdo (para Lora training)
                var txtPath = Path.Combine(outputDir, $"{baseName}.txt");
                await File.WriteAllTextAsync(txtPath, registro.Conteudo);

                saved = true;
                break; // Só salvar a primeira imagem por nó
            }

            if (saved) break; // Só precisamos de uma imagem por registro
        }

        return saved;
    }
}
