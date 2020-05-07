FROM mcr.microsoft.com/dotnet/core/sdk:latest AS build
WORKDIR /source

# copy csproj and restore as distinct layers
COPY *.csproj .
RUN dotnet restore

COPY . .
RUN dotnet publish -c release -o /app --no-restore

# final stage/image
FROM mcr.microsoft.com/dotnet/core/runtime:latest
WORKDIR /app
COPY --from=build /app .
ENTRYPOINT ["./worker"]
