using System.Text.Json.Serialization;

namespace ConfyManager.Models;

public record MassaDataset(
    [property: JsonPropertyName("config")] MassaConfig Config,
    [property: JsonPropertyName("registros")] List<MassaRegistro> Registros
);

public record MassaConfig(
    [property: JsonPropertyName("imagemReferencia")] string ImagemReferencia,
    [property: JsonPropertyName("largura")] int Largura,
    [property: JsonPropertyName("altura")] int Altura,
    [property: JsonPropertyName("totalRegistros")] int TotalRegistros,
    [property: JsonPropertyName("sexo")] string Sexo,
    [property: JsonPropertyName("geradoEm")] string GeradoEm
);

public record MassaRegistro(
    [property: JsonPropertyName("id")] int Id,
    [property: JsonPropertyName("prompt")] string Prompt,
    [property: JsonPropertyName("conteudo")] string Conteudo
);
