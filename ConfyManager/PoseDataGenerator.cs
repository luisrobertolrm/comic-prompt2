using System.Text.Json;
using ConfyManager.Models;

namespace ConfyManager;

public static class PoseDataGenerator
{
    private static readonly string[] Poses =
    [
        "standing, arms crossed, confident pose",
        "standing, hands on hips, assertive stance",
        "standing, one hand raised, waving",
        "standing, leaning slightly forward, curious expression",
        "standing, looking over shoulder, turning back",
        "standing, arms behind back, relaxed",
        "standing, hand on chest, emotional gesture",
        "standing, pointing forward, dynamic pose",
        "standing, stretching arms up, relaxed",
        "walking, mid-stride, natural movement",
        "walking, looking back over shoulder",
        "running, dynamic action pose, wind in hair",
        "sitting, legs crossed, elegant pose",
        "sitting on chair, leaning back, relaxed",
        "sitting on ground, knees up, casual",
        "sitting, hand on chin, thinking pose",
        "sitting on bench, looking to the side",
        "kneeling, one knee down, determined look",
        "kneeling, both knees, hands clasped",
        "crouching, ready to spring, action pose",
        "leaning on wall, arms crossed, cool pose",
        "leaning on railing, looking at horizon",
        "leaning forward, hands on table",
        "fighting stance, fists up, intense look",
        "martial arts kick, dynamic action",
        "sword drawing pose, hand on hilt",
        "holding sword, battle ready stance",
        "archery pose, drawing bow",
        "dancing, twirling, graceful movement",
        "dancing, arms extended, elegant",
        "jumping, mid-air, energetic",
        "floating, serene expression, weightless",
        "lying down, side pose, relaxed",
        "lying on back, looking up, dreamy",
        "hugging knees, sitting, contemplative",
        "arms outstretched, embracing wind",
        "praying, hands together, serene",
        "reading, holding book, focused",
        "writing, pen in hand, concentrated",
        "cooking, holding utensil, busy",
        "playing instrument, guitar pose",
        "playing instrument, violin pose",
        "training, punching pose, intense",
        "meditating, cross-legged, peaceful",
        "saluting, military style, disciplined",
        "stretching, yoga pose, flexible",
        "climbing, reaching up, determined",
        "riding, horseback pose, commanding",
        "casting magic, hands glowing, mystical",
        "looking at viewer, slight smile, portrait"
    ];

    private static readonly string[] Roupas =
    [
        "casual outfit, t-shirt, jeans",
        "school uniform, pleated skirt, blazer",
        "kimono, traditional obi sash",
        "formal dress, long elegant dress",
        "athletic wear, sports bra, shorts",
        "armor, plate armor, medieval style",
        "hoodie, casual streetwear, sneakers",
        "business suit, formal attire, tie",
        "summer dress, floral pattern, light fabric",
        "winter coat, scarf, warm clothing",
        "maid outfit, frilly apron, headband",
        "military uniform, combat gear",
        "traditional chinese hanfu, flowing robes",
        "sailor outfit, navy style, striped",
        "leather jacket, punk style, boots",
        "fantasy robe, wizard attire, cloak",
        "gothic dress, dark lace, corset",
        "nurse outfit, white uniform, cap",
        "detective coat, trench coat, hat",
        "samurai armor, feudal japan attire",
        "witch outfit, pointed hat, flowing cape",
        "cyberpunk outfit, neon accents, tech gear",
        "princess gown, tiara, royal attire",
        "ninja outfit, dark wrappings, stealth gear",
        "pirate outfit, captain coat, bandana"
    ];

    private static readonly string[] EstilosCabelo =
    [
        "hair down, loose flowing hair",
        "ponytail, high ponytail",
        "twin tails, pigtails",
        "bun hairstyle, hair up",
        "braided hair, single braid",
        "side braid, over shoulder",
        "short hair, bob cut",
        "long hair, waist length",
        "curly hair, voluminous",
        "hair with bangs, straight bangs",
        "messy hair, windswept",
        "half up half down hairstyle",
        "french braid, elegant updo",
        "low ponytail, tied at nape",
        "space buns, double buns"
    ];

    private static readonly string[] Acessorios =
    [
        "necklace, pendant",
        "glasses, round frame",
        "earrings, dangling earrings",
        "hair ornament, flower pin",
        "wristband, leather bracelet",
        "headband, fabric headband",
        "choker, black choker",
        "ribbon, hair ribbon",
        "hat, wide brim hat",
        "scarf, silk scarf",
        "belt, decorative belt",
        "gloves, fingerless gloves",
        "ring, silver ring",
        "brooch, crystal brooch",
        "hairclip, butterfly hairclip",
        "no accessories"
    ];

    private static readonly string[] Iluminacao =
    [
        "cinematic lighting",
        "soft lighting, warm tones",
        "dramatic side lighting",
        "golden hour lighting, sunset",
        "studio lighting, clean shadows",
        "moonlight, cool blue tones",
        "neon lighting, vibrant colors",
        "natural daylight, outdoor",
        "backlit, silhouette rim light",
        "candlelight, warm ambient glow"
    ];

    private static readonly string[] QualityTags =
    [
        "masterpiece, best quality, 1girl, solo"
    ];

    public static string Generate(string imagePath, int count, string outputName, int width, int height)
    {
        var random = new Random();
        var registros = new List<MassaRegistro>();

        for (int i = 1; i <= count; i++)
        {
            var pose = Poses[random.Next(Poses.Length)];
            var roupa = Roupas[random.Next(Roupas.Length)];
            var cabelo = EstilosCabelo[random.Next(EstilosCabelo.Length)];
            var acessorio = Acessorios[random.Next(Acessorios.Length)];
            var luz = Iluminacao[random.Next(Iluminacao.Length)];
            var quality = QualityTags[0];

            // Prompt para ComfyUI (com quality tags + pose + iluminação)
            var prompt = $"{quality}, {pose}, {luz}";

            // Conteúdo para .txt do dataset (roupa, pose, acessórios, cabelo — SEM características físicas)
            var conteudoParts = new List<string> { pose, roupa, cabelo };
            if (acessorio != "no accessories")
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
