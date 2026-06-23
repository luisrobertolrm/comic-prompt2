using System.Text.Json;
using ConfyManager.Models;

namespace ConfyManager;

public static class PoseDataGenerator
{
    private static readonly string[] Poses =
    [
        "standing, front view",
        "standing, looking at viewer",
        "standing, arms crossed",
        "standing, hands on hips",
        "standing, from side",
        "standing, from behind",
        "standing, looking back",
        "standing, waving",
        "sitting",
        "sitting, legs crossed",
        "sitting, from side",
        "sitting on chair",
        "sitting on ground",
        "kneeling",
        "crouching",
        "walking",
        "running",
        "jumping",
        "leaning on wall",
        "lying down",
        "fighting stance",
        "dancing",
        "reading",
        "arms up",
        "praying"
    ];

    private static readonly string[] Roupas =
    [
        "casual clothes",
        "school uniform",
        "kimono",
        "formal dress",
        "athletic wear",
        "hoodie",
        "business suit",
        "summer dress",
        "winter coat",
        "military uniform",
        "leather jacket",
        "fantasy robe",
        "gothic dress",
        "samurai armor",
        "ninja outfit"
    ];

    private static readonly string[] EstilosCabelo =
    [
        "hair down",
        "ponytail",
        "twin tails",
        "bun",
        "braided hair",
        "short hair",
        "long hair",
        "messy hair",
        "hair up"
    ];

    private static readonly string[] Acessorios =
    [
        "necklace",
        "glasses",
        "earrings",
        "hair ornament",
        "headband",
        "choker",
        "hat",
        "gloves",
        ""
    ];

    public static string Generate(string imagePath, int count, string outputName, int width, int height, string sexo)
    {
        var random = new Random();
        var registros = new List<MassaRegistro>();
        var tag = sexo == "M" ? "1boy, solo" : "1girl, solo";

        for (int i = 1; i <= count; i++)
        {
            var pose = Poses[random.Next(Poses.Length)];
            var roupa = Roupas[random.Next(Roupas.Length)];
            var cabelo = EstilosCabelo[random.Next(EstilosCabelo.Length)];
            var acessorio = Acessorios[random.Next(Acessorios.Length)];

            // Prompt para ComfyUI — curto e direto
            var prompt = $"{tag}, {pose}";

            // Conteúdo para .txt do dataset (roupa, pose, cabelo, acessórios — SEM características físicas)
            var conteudoParts = new List<string> { pose, roupa, cabelo };
            if (!string.IsNullOrEmpty(acessorio))
                conteudoParts.Add(acessorio);

            var conteudo = string.Join(", ", conteudoParts);

            registros.Add(new MassaRegistro(i, prompt, conteudo));
        }

        var dataset = new MassaDataset(
            new MassaConfig(
                ImagemReferencia: Path.GetFullPath(imagePath),
                Largura: width,
                Altura: height,
                TotalRegistros: count,
                Sexo: sexo,
                GeradoEm: DateTime.Now.ToString("yyyy-MM-ddTHH:mm:ss")
            ),
            registros
        );

        var outputPath = outputName.EndsWith(".json", StringComparison.OrdinalIgnoreCase)
            ? outputName
            : $"{outputName}.json";

        var jsonOptions = new JsonSerializerOptions
        {
            WriteIndented = true,
            Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping
        };

        var json = JsonSerializer.Serialize(dataset, jsonOptions);
        File.WriteAllText(outputPath, json, System.Text.Encoding.UTF8);

        return Path.GetFullPath(outputPath);
    }
}
