using Microsoft.AspNetCore.Components.Web;
using Microsoft.AspNetCore.Components.WebAssembly.Hosting;
using BluesLab;
using BluesLab.Services;

var builder = WebAssemblyHostBuilder.CreateDefault(args);
builder.RootComponents.Add<App>("#app");
builder.RootComponents.Add<HeadOutlet>("head::after");

builder.Services.AddScoped(sp => new HttpClient { BaseAddress = new Uri(builder.HostEnvironment.BaseAddress) });
builder.Services.AddScoped<SyncPairDataService>();
builder.Services.AddScoped<GridStateService>();
builder.Services.AddScoped<DamageCalculatorService>();
builder.Services.AddScoped<StageService>();

await builder.Build().RunAsync();