using ConfyManager;
using Spectre.Console;

const string VERSION = "1.0.0";

Console.OutputEncoding = System.Text.Encoding.UTF8;
Console.Title = "ConfyManager";

var resolutionPresets = new Dictionary<string, (int w, int h)>
{
    ["SDXL Retrato (832×1216)"] = (832, 1216),
    ["Quadrado (1024×1024)"] = (1024, 1024),
    ["Retrato Alto (768×1344)"] = (768, 1344),
    ["Retrato Médio (896×1152)"] = (896, 1152),
    ["SD 1.5 (512×512)"] = (512, 512),
    ["Personalizado"] = (0, 0)
};

while (true)
{
    Console.Clear();
    RenderHeader();
    RenderCommandHelp();
    RenderSeparator();

    var input = AnsiConsole.Prompt(
        new TextPrompt<string>("[bold cyan]>[/]")
            .AllowEmpty()
    );

    var trimmed = input.Trim();
    var trimmedLower = trimmed.ToLowerInvariant();

    if (trimmedLower == "/exit")
    {
        Console.Clear();
        AnsiConsole.Write(
            new FigletText("Bye!")
                .Centered()
                .Color(Color.MediumPurple1)
        );
        AnsiConsole.MarkupLine("\n  [dim]ConfyManager encerrado.[/]\n");
        break;
    }

    if (trimmedLower == "/massa")
    {
        Console.Clear();
        RenderHeader();
        HandleMassa();
        WaitForKey();
        continue;
    }

    if (trimmedLower.StartsWith("/gerar"))
    {
        Console.Clear();
        RenderHeader();
        HandleGerar(trimmed);
        WaitForKey();
        continue;
    }

    if (trimmedLower.StartsWith("/processar"))
    {
        Console.Clear();
        RenderHeader();
        HandleProcessar(trimmed).GetAwaiter().GetResult();
        WaitForKey();
        continue;
    }

    if (!string.IsNullOrWhiteSpace(trimmed))
    {
        Console.Clear();
        RenderHeader();
        AnsiConsole.MarkupLine($"\n  [red]✗[/] Comando desconhecido: [yellow]{Markup.Escape(trimmed)}[/]");
        AnsiConsole.MarkupLine("  [dim]Digite [bold]/gerar[/], [bold]/processar[/] ou [bold]/exit[/][/]\n");
        WaitForKey();
    }
}

// ─── Funções ────────────────────────────────────────────────

void RenderHeader()
{
    var headerPanel = new Panel(
        new FigletText("ConfyManager")
            .Centered()
            .Color(Color.MediumPurple1)
    )
    {
        Border = BoxBorder.Double,
        BorderStyle = new Style(Color.DarkSlateGray1),
        Padding = new Padding(1, 0),
        Header = new PanelHeader($" [bold dim]v{VERSION}[/] ", Justify.Right)
    };

    AnsiConsole.Write(headerPanel);
    AnsiConsole.WriteLine();
}

void RenderCommandHelp()
{
    var table = new Table()
        .Border(TableBorder.Rounded)
        .BorderColor(Color.Grey35)
        .AddColumn(new TableColumn("[bold cyan]Comando[/]").Centered())
        .AddColumn(new TableColumn("[bold cyan]Descrição[/]").LeftAligned())
        .AddRow("[green]/massa[/]", "[dim]Gerar imagens para Lora (dataset) — placeholder[/]")
        .AddRow("[green]/gerar[/] [dim]img|qtd|nome[/]", "[dim]Gerar arquivo JSON de prompts para massa Lora[/]")
        .AddRow("[green]/processar[/] [dim]wf|ds|dir[/]", "[dim]Enviar dataset ao ComfyUI e gerar imagens + .txt[/]")
        .AddRow("[red]/exit[/]", "[dim]Sair do ConfyManager[/]");

    AnsiConsole.Write(Align.Center(table));
    AnsiConsole.WriteLine();
}

void RenderSeparator()
{
    AnsiConsole.Write(new Rule("[dim grey]digite um comando[/]")
    {
        Style = Style.Parse("grey35"),
        Justification = Justify.Center
    });
    AnsiConsole.WriteLine();
}

void HandleMassa()
{
    AnsiConsole.WriteLine();

    AnsiConsole.Write(new Rule("[bold mediumpurple1]🎨 Gerador de Imagens para Lora[/]")
    {
        Style = Style.Parse("mediumpurple1"),
        Justification = Justify.Center
    });

    AnsiConsole.WriteLine();

    var outputPanel = new Panel(
        new Rows(
            new Markup("[bold green]✓[/] Pipeline de geração de imagens iniciado"),
            new Markup(""),
            new Markup("[dim]Etapas do processo:[/]"),
            new Markup("  [cyan]1.[/] Carregar configuração do modelo base"),
            new Markup("  [cyan]2.[/] Preparar prompts de treinamento"),
            new Markup("  [cyan]3.[/] Gerar imagens de referência (512×512)"),
            new Markup("  [cyan]4.[/] Aplicar augmentação de dados"),
            new Markup("  [cyan]5.[/] Salvar dataset no diretório de saída"),
            new Markup(""),
            new Markup("[bold yellow]⚠  Funcionalidade ainda não implementada.[/]"),
            new Markup("[dim]   Este é um placeholder para a futura integração com ComfyUI.[/]")
        )
    )
    {
        Border = BoxBorder.Rounded,
        BorderStyle = new Style(Color.MediumPurple1),
        Padding = new Padding(2, 1),
        Header = new PanelHeader(" [bold]Massa → Lora Dataset[/] ", Justify.Center)
    };

    AnsiConsole.Write(Align.Center(outputPanel));

    AnsiConsole.WriteLine();

    AnsiConsole.Status()
        .Spinner(Spinner.Known.Dots)
        .SpinnerStyle(Style.Parse("mediumpurple1"))
        .Start("[dim]Simulando pipeline...[/]", ctx =>
        {
            ctx.Status("[cyan]Carregando modelo base...[/]");
            Thread.Sleep(800);
            ctx.Status("[cyan]Preparando prompts...[/]");
            Thread.Sleep(600);
            ctx.Status("[cyan]Gerando imagens...[/]");
            Thread.Sleep(1000);
            ctx.Status("[green]Concluído![/]");
            Thread.Sleep(400);
        });

    AnsiConsole.MarkupLine("\n  [bold green]✓[/] Simulação concluída com sucesso.\n");
}

void HandleGerar(string fullInput)
{
    AnsiConsole.WriteLine();

    AnsiConsole.Write(new Rule("[bold mediumpurple1]📄 Gerador de Prompts para Massa Lora[/]")
    {
        Style = Style.Parse("mediumpurple1"),
        Justification = Justify.Center
    });

    AnsiConsole.WriteLine();

    // Extrair argumentos após "/gerar"
    var argsStr = fullInput.Length > 6 ? fullInput[6..].Trim() : "";

    string imagePath;
    int quantidade;
    string nomeFinal;

    if (string.IsNullOrWhiteSpace(argsStr))
    {
        // Modo interativo
        AnsiConsole.MarkupLine("  [dim]Nenhum argumento fornecido. Modo interativo.[/]\n");

        imagePath = AnsiConsole.Prompt(
            new TextPrompt<string>("  [cyan]Caminho da imagem de referência:[/]")
                .Validate(path =>
                    File.Exists(path)
                        ? ValidationResult.Success()
                        : ValidationResult.Error("[red]Arquivo não encontrado[/]"))
        );

        quantidade = AnsiConsole.Prompt(
            new TextPrompt<int>("  [cyan]Quantidade de registros:[/]")
                .DefaultValue(20)
                .Validate(n =>
                    n is > 0 and <= 500
                        ? ValidationResult.Success()
                        : ValidationResult.Error("[red]Entre 1 e 500[/]"))
        );

        nomeFinal = AnsiConsole.Prompt(
            new TextPrompt<string>("  [cyan]Nome do arquivo de saída:[/]")
                .DefaultValue("massa_lora")
        );
    }
    else
    {
        // Parsing: /gerar caminho | quantidade | nome
        var parts = argsStr.Split('|', StringSplitOptions.TrimEntries);

        if (parts.Length < 3)
        {
            AnsiConsole.MarkupLine("  [red]✗[/] Formato inválido. Use: [yellow]/gerar caminhoImagem | quantidade | nomeFinal[/]");
            AnsiConsole.MarkupLine("  [dim]Exemplo: /gerar C:\\imgs\\ref.png | 20 | dataset_samurai[/]\n");
            return;
        }

        imagePath = parts[0];
        if (!File.Exists(imagePath))
        {
            AnsiConsole.MarkupLine($"  [red]✗[/] Arquivo não encontrado: [yellow]{Markup.Escape(imagePath)}[/]\n");
            return;
        }

        if (!int.TryParse(parts[1], out quantidade) || quantidade <= 0 || quantidade > 500)
        {
            AnsiConsole.MarkupLine($"  [red]✗[/] Quantidade inválida: [yellow]{Markup.Escape(parts[1])}[/] (deve ser entre 1 e 500)\n");
            return;
        }

        nomeFinal = parts[2];
    }

    // Seleção de resolução
    AnsiConsole.WriteLine();
    var presetChoice = AnsiConsole.Prompt(
        new SelectionPrompt<string>()
            .Title("  [cyan]Selecione a resolução:[/]")
            .HighlightStyle(Style.Parse("mediumpurple1"))
            .AddChoices(resolutionPresets.Keys)
    );

    int width, height;
    var preset = resolutionPresets[presetChoice];

    if (preset.w == 0)
    {
        width = AnsiConsole.Prompt(
            new TextPrompt<int>("  [cyan]Largura (px):[/]")
                .Validate(n =>
                    n is > 0 and <= 4096
                        ? ValidationResult.Success()
                        : ValidationResult.Error("[red]Entre 1 e 4096[/]"))
        );
        height = AnsiConsole.Prompt(
            new TextPrompt<int>("  [cyan]Altura (px):[/]")
                .Validate(n =>
                    n is > 0 and <= 4096
                        ? ValidationResult.Success()
                        : ValidationResult.Error("[red]Entre 1 e 4096[/]"))
        );
    }
    else
    {
        width = preset.w;
        height = preset.h;
    }

    // Mostrar resumo
    AnsiConsole.WriteLine();
    var summaryTable = new Table()
        .Border(TableBorder.Rounded)
        .BorderColor(Color.Grey35)
        .AddColumn(new TableColumn("[bold cyan]Parâmetro[/]").LeftAligned())
        .AddColumn(new TableColumn("[bold cyan]Valor[/]").LeftAligned())
        .AddRow("[dim]Imagem[/]", Markup.Escape(Path.GetFileName(imagePath)))
        .AddRow("[dim]Caminho completo[/]", Markup.Escape(Path.GetFullPath(imagePath)))
        .AddRow("[dim]Quantidade[/]", quantidade.ToString())
        .AddRow("[dim]Resolução[/]", $"{width}×{height}")
        .AddRow("[dim]Arquivo de saída[/]", Markup.Escape(nomeFinal.EndsWith(".json", StringComparison.OrdinalIgnoreCase) ? nomeFinal : $"{nomeFinal}.json"));

    AnsiConsole.Write(Align.Center(summaryTable));
    AnsiConsole.WriteLine();

    // Gerar
    try
    {
        string outputPath = "";

        AnsiConsole.Status()
            .Spinner(Spinner.Known.Dots)
            .SpinnerStyle(Style.Parse("mediumpurple1"))
            .Start("[cyan]Gerando prompts...[/]", ctx =>
            {
                ctx.Status("[cyan]Combinando poses, roupas e acessórios...[/]");
                Thread.Sleep(300);
                outputPath = PoseDataGenerator.Generate(imagePath, quantidade, nomeFinal, width, height);
                ctx.Status("[green]Salvando arquivo JSON...[/]");
                Thread.Sleep(200);
            });

        AnsiConsole.MarkupLine($"\n  [bold green]✓[/] Arquivo gerado com sucesso!");
        AnsiConsole.MarkupLine($"  [dim]→[/] [link]{Markup.Escape(outputPath)}[/]\n");

        // Preview dos primeiros registros
        var previewCount = Math.Min(3, quantidade);
        AnsiConsole.Write(new Rule($"[dim]Preview ({previewCount} de {quantidade} registros)[/]")
        {
            Style = Style.Parse("grey35"),
            Justification = Justify.Center
        });
        AnsiConsole.WriteLine();

        var json = File.ReadAllText(outputPath);
        var dataset = System.Text.Json.JsonSerializer.Deserialize<ConfyManager.Models.MassaDataset>(json);
        if (dataset != null)
        {
            foreach (var reg in dataset.Registros.Take(previewCount))
            {
                var regPanel = new Panel(
                    new Rows(
                        new Markup($"[bold cyan]prompt:[/] [dim]{Markup.Escape(reg.Prompt)}[/]"),
                        new Markup($"[bold green]conteudo:[/] [dim]{Markup.Escape(reg.Conteudo)}[/]")
                    )
                )
                {
                    Border = BoxBorder.Rounded,
                    BorderStyle = new Style(Color.Grey35),
                    Padding = new Padding(1, 0),
                    Header = new PanelHeader($" [bold]#{reg.Id}[/] ", Justify.Left)
                };

                AnsiConsole.Write(regPanel);
            }

            if (quantidade > previewCount)
                AnsiConsole.MarkupLine($"\n  [dim]... e mais {quantidade - previewCount} registros no arquivo.[/]");
        }

        AnsiConsole.WriteLine();
    }
    catch (Exception ex)
    {
        AnsiConsole.MarkupLine($"\n  [red]✗[/] Erro ao gerar: [yellow]{Markup.Escape(ex.Message)}[/]\n");
    }
}

async Task HandleProcessar(string fullInput)
{
    AnsiConsole.WriteLine();

    AnsiConsole.Write(new Rule("[bold mediumpurple1]⚙ Processar Dataset no ComfyUI[/]")
    {
        Style = Style.Parse("mediumpurple1"),
        Justification = Justify.Center
    });

    AnsiConsole.WriteLine();

    // Extrair argumentos após "/processar"
    var argsStr = fullInput.Length > 10 ? fullInput[10..].Trim() : "";

    string workflowPath;
    string datasetPath;
    string outputDir;

    if (string.IsNullOrWhiteSpace(argsStr))
    {
        // Modo interativo
        AnsiConsole.MarkupLine("  [dim]Nenhum argumento fornecido. Modo interativo.[/]\n");

        workflowPath = AnsiConsole.Prompt(
            new TextPrompt<string>("  [cyan]Caminho do workflow API (.json):[/]")
                .Validate(path =>
                    File.Exists(path)
                        ? ValidationResult.Success()
                        : ValidationResult.Error("[red]Arquivo não encontrado[/]"))
        );

        datasetPath = AnsiConsole.Prompt(
            new TextPrompt<string>("  [cyan]Caminho do dataset gerado (.json):[/]")
                .Validate(path =>
                    File.Exists(path)
                        ? ValidationResult.Success()
                        : ValidationResult.Error("[red]Arquivo não encontrado[/]"))
        );

        outputDir = AnsiConsole.Prompt(
            new TextPrompt<string>("  [cyan]Diretório de saída:[/]")
                .DefaultValue("output_lora")
        );
    }
    else
    {
        // Parsing: /processar workflow.json | dataset.json | outputDir
        var parts = argsStr.Split('|', StringSplitOptions.TrimEntries);

        if (parts.Length < 3)
        {
            AnsiConsole.MarkupLine("  [red]✗[/] Formato inválido. Use: [yellow]/processar workflow.json | dataset.json | diretorioSaida[/]");
            AnsiConsole.MarkupLine("  [dim]Exemplo: /processar controlnet_api.json | massa_lora.json | output_lora[/]\n");
            return;
        }

        workflowPath = parts[0];
        if (!File.Exists(workflowPath))
        {
            AnsiConsole.MarkupLine($"  [red]✗[/] Workflow não encontrado: [yellow]{Markup.Escape(workflowPath)}[/]\n");
            return;
        }

        datasetPath = parts[1];
        if (!File.Exists(datasetPath))
        {
            AnsiConsole.MarkupLine($"  [red]✗[/] Dataset não encontrado: [yellow]{Markup.Escape(datasetPath)}[/]\n");
            return;
        }

        outputDir = parts[2];
    }

    // URL do ComfyUI
    var comfyUrl = AnsiConsole.Prompt(
        new TextPrompt<string>("  [cyan]URL do ComfyUI:[/]")
            .DefaultValue("http://127.0.0.1:8188")
    );

    // Resumo
    AnsiConsole.WriteLine();
    var summaryTable = new Table()
        .Border(TableBorder.Rounded)
        .BorderColor(Color.Grey35)
        .AddColumn(new TableColumn("[bold cyan]Parâmetro[/]").LeftAligned())
        .AddColumn(new TableColumn("[bold cyan]Valor[/]").LeftAligned())
        .AddRow("[dim]Workflow[/]", Markup.Escape(Path.GetFileName(workflowPath)))
        .AddRow("[dim]Dataset[/]", Markup.Escape(Path.GetFileName(datasetPath)))
        .AddRow("[dim]Saída[/]", Markup.Escape(Path.GetFullPath(outputDir)))
        .AddRow("[dim]ComfyUI[/]", Markup.Escape(comfyUrl));

    AnsiConsole.Write(Align.Center(summaryTable));
    AnsiConsole.WriteLine();

    // Confirmar
    var confirmar = AnsiConsole.Confirm("  [yellow]Iniciar processamento?[/]", true);
    if (!confirmar)
    {
        AnsiConsole.MarkupLine("\n  [dim]Cancelado pelo usuário.[/]\n");
        return;
    }

    AnsiConsole.WriteLine();

    try
    {
        int processados = 0;

        await AnsiConsole.Progress()
            .AutoClear(false)
            .HideCompleted(false)
            .Columns(
                new TaskDescriptionColumn(),
                new ProgressBarColumn(),
                new PercentageColumn(),
                new SpinnerColumn(Spinner.Known.Dots)
            )
            .StartAsync(async ctx =>
            {
                var task = ctx.AddTask("[cyan]Processando...[/]", maxValue: 100);

                processados = await ConfyManager.WorkflowProcessor.ProcessAsync(
                    workflowPath,
                    datasetPath,
                    outputDir,
                    comfyUrl,
                    onStatus: status =>
                    {
                        task.Description = $"[cyan]{Markup.Escape(status)}[/]";
                    },
                    onProgress: (current, total) =>
                    {
                        task.MaxValue = total;
                        task.Value = current;
                    }
                );

                task.Description = "[green]Concluído![/]";
                task.Value = task.MaxValue;
            });

        AnsiConsole.WriteLine();
        AnsiConsole.MarkupLine($"  [bold green]✓[/] Processamento concluído!");
        AnsiConsole.MarkupLine($"  [dim]→[/] {processados} imagens geradas em [link]{Markup.Escape(Path.GetFullPath(outputDir))}[/]");
        AnsiConsole.MarkupLine($"  [dim]→[/] {processados} arquivos .txt criados para Lora\n");

        // Listar arquivos gerados
        if (Directory.Exists(outputDir))
        {
            var files = Directory.GetFiles(outputDir)
                .OrderBy(f => f)
                .Take(10)
                .ToArray();

            if (files.Length > 0)
            {
                var fileTable = new Table()
                    .Border(TableBorder.Rounded)
                    .BorderColor(Color.Grey35)
                    .AddColumn(new TableColumn("[bold cyan]Arquivo[/]").LeftAligned())
                    .AddColumn(new TableColumn("[bold cyan]Tamanho[/]").RightAligned());

                foreach (var f in files)
                {
                    var info = new FileInfo(f);
                    var size = info.Length > 1024
                        ? $"{info.Length / 1024.0:F1} KB"
                        : $"{info.Length} B";
                    fileTable.AddRow(
                        Markup.Escape(Path.GetFileName(f)),
                        $"[dim]{size}[/]"
                    );
                }

                var totalFiles = Directory.GetFiles(outputDir).Length;
                if (totalFiles > 10)
                    fileTable.Caption = new TableTitle($"[dim]... e mais {totalFiles - 10} arquivos[/]");

                AnsiConsole.Write(Align.Center(fileTable));
            }
        }

        AnsiConsole.WriteLine();
    }
    catch (Exception ex)
    {
        AnsiConsole.MarkupLine($"\n  [red]✗[/] Erro: [yellow]{Markup.Escape(ex.Message)}[/]\n");
    }
}

void WaitForKey()
{
    AnsiConsole.MarkupLine("  [dim]Pressione qualquer tecla para continuar...[/]");
    Console.ReadKey(true);
}
