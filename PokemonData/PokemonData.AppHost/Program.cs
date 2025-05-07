var builder = DistributedApplication.CreateBuilder(args);

builder.AddProject<Projects.PokemonData>("pokemondata");

builder.Build().Run();
