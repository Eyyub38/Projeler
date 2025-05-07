using System;
using System.Windows.Forms;
using PokemonData.ViewModels;
using PokemonData.Services;

namespace PokemonData
{
    public partial class MainForm : Form
    {
        private readonly MainViewModel _viewModel;
        private readonly IPokemonService _pokemonService;

        public MainForm()
        {
            InitializeComponent();
            
            // Initialize services
            _pokemonService = new PokemonService();
            
            // Initialize ViewModel
            _viewModel = new MainViewModel(_pokemonService);
            
            // Setup data binding
            pokemonListBox.DataSource = _viewModel.Pokemons;
            pokemonListBox.DisplayMember = "Name";
            
            // Bind loading state
            loadingProgressBar.DataBindings.Add("Visible", _viewModel, "IsLoading");
            
            // Load data when form loads
            this.Load += async (s, e) => await _viewModel.LoadPokemons(progress => 
            {
                if (loadingProgressBar.InvokeRequired)
                {
                    loadingProgressBar.Invoke(new Action(() => 
                    {
                        loadingProgressBar.Value = progress;
                        loadingProgressBar.Visible = true;
                    }));
                }
                else
                {
                    loadingProgressBar.Value = progress;
                    loadingProgressBar.Visible = true;
                }
            });
        }

        private void pokemonListBox_SelectedIndexChanged(object sender, EventArgs e)
        {
            if (pokemonListBox.SelectedItem is Pokemon selectedPokemon)
            {
                _viewModel.SelectedPokemon = selectedPokemon;
                UpdatePokemonDetails(selectedPokemon);
            }
        }

        private void UpdatePokemonDetails(Pokemon pokemon)
        {
            if (pokemon == null) return;

            nameLabel.Text = $"Name: {pokemon.Name}";
            heightLabel.Text = $"Height: {pokemon.Height / 10.0:F1} m";
            weightLabel.Text = $"Weight: {pokemon.Weight / 10.0:F1} kg";

            // Update stats
            statsListBox.Items.Clear();
            foreach (var stat in pokemon.Stats)
            {
                statsListBox.Items.Add($"{stat.Stat.Name}: {stat.BaseStat}");
            }

            // Update types
            typesListBox.Items.Clear();
            foreach (var type in pokemon.Types)
            {
                typesListBox.Items.Add(type.Type.Name);
            }

            // Update species info
            speciesInfoListBox.Items.Clear();
            if (pokemon.Species != null)
            {
                speciesInfoListBox.Items.Add($"Base Happiness: {pokemon.Species.BaseHappiness}");
                speciesInfoListBox.Items.Add($"Capture Rate: {pokemon.Species.CaptureRate}");
                speciesInfoListBox.Items.Add($"Growth Rate: {pokemon.Species.GrowthRate?.Name}");
            }

            // Update egg groups
            eggGroupsListBox.Items.Clear();
            if (pokemon.Species?.EggGroups != null)
            {
                foreach (var eggGroup in pokemon.Species.EggGroups)
                {
                    eggGroupsListBox.Items.Add(eggGroup.Name);
                }
            }

            // Update learnable moves
            learnableMovesListBox.Items.Clear();
            if (pokemon.Moves != null)
            {
                foreach (var move in pokemon.Moves)
                {
                    learnableMovesListBox.Items.Add(move.Move.Name);
                }
            }

            // Update Pokedex description
            if (pokemon.Species?.FlavorTextEntries != null)
            {
                var englishEntry = pokemon.Species.FlavorTextEntries
                    .FirstOrDefault(f => f.Language.Name == "en");
                pokedexDescriptionTextBox.Text = englishEntry?.FlavorText ?? "No description available";
            }
            else
            {
                pokedexDescriptionTextBox.Text = "No description available";
            }

            // Load Pokemon image
            if (!string.IsNullOrEmpty(pokemon.Sprites?.FrontDefault))
            {
                try
                {
                    using (var client = new System.Net.WebClient())
                    {
                        var imageBytes = client.DownloadData(pokemon.Sprites.FrontDefault);
                        using (var ms = new System.IO.MemoryStream(imageBytes))
                        {
                            pokemonPictureBox.Image = System.Drawing.Image.FromStream(ms);
                        }
                    }
                }
                catch (Exception ex)
                {
                    MessageBox.Show($"Error loading Pokemon image: {ex.Message}", "Error", 
                        MessageBoxButtons.OK, MessageBoxIcon.Error);
                }
            }
        }

        private async void LoadInitialData()
        {
            try
            {
                // Pokemon verilerini yükle
                await _viewModel.LoadPokemons(progress =>
                {
                    if (loadingProgressBar.InvokeRequired)
                    {
                        loadingProgressBar.Invoke(new Action(() =>
                        {
                            loadingProgressBar.Value = progress;
                            loadingProgressBar.Visible = true;
                        }));
                    }
                    else
                    {
                        loadingProgressBar.Value = progress;
                        loadingProgressBar.Visible = true;
                    }
                });

                // Move verilerini yükle
                await _viewModel.LoadMoves();

                // Item verilerini yükle
                await _viewModel.LoadItems();
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Veri yüklenirken hata oluştu: {ex.Message}", "Hata", 
                    MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
            finally
            {
                loadingProgressBar.Visible = false;
            }
        }
    }
} 